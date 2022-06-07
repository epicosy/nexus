import ast
from datetime import datetime
from pathlib import Path
from typing import List, Union
from io import BytesIO

from cement import Handler

from docker.errors import APIError
from docker.models.containers import Container
from docker.models.volumes import Volume

from nexus.core.data.results import CommandData
from nexus.core.exc import NexusError, CommandError
from nexus.core.interfaces.handlers import HandlersInterface
from nexus.core.utils.misc import str_to_tarfile


class ContainerHandler(HandlersInterface, Handler):
    class Meta:
        label = 'container'

    def setup(self, container: Container, cmds: List[str], env: dict = None) -> bool:
        #env_file = self.write(container=container, data="export DEBIAN_FRONTEND=noninteractive", path=Path('/tmp'),
        #                      name='env')
        for cmd in cmds:
            cmd_data = self.__call__(container.id, cmd_str=cmd, raise_err=True, env=env)

            if cmd_data.error or cmd_data.return_code != 0:
                self.app.log.error(cmd_data.error)
                return False

            self.app.log.info(cmd_data.output)

        return True

    def is_setup(self, container: Container, kind: str):
        server_app = 'synapser' if kind == 'tool' else 'orbis'
        cmd_data = self.__call__(container.id, cmd_str=f"which {server_app}", raise_err=True)

        if cmd_data.output and server_app in cmd_data.output:
            self.app.log.info(f"{container.name} {kind} container already setup")
            return True

        return False

    def build(self, path: Path, tag: str):
        for line in self.app.docker.api.build(path=str(path), rm=True, tag=tag):
            # decoded = ast.literal_eval(line.decode('utf-8'))
            # if 'stream' in decoded:
            #    self.app.log.info(decoded['stream'])
            # else:
            #    self.app.log.info(decoded)

            decoded = line.decode('utf-8')
            self.app.log.info(decoded)

    def create(self, image: str, container_configs: dict, name: str, volume: Volume) -> str:
        binds = {volume.name: {'bind': f"/{volume.name}", 'mode': 'rw'}}
        bind_port = container_configs['api']['port']
        host_config = self.app.docker.api.create_host_config(binds=binds)
        output = self.app.docker.api.create_container(image, name=name, volumes=[f"/{volume.name}"],
                                                      host_config=host_config, tty=True, detach=True,
                                                      ports=[bind_port])

        self.app.log.info(f"Created container for {name} with id {output['Id'][:10]}")

        if 'Warnings' in output and output['Warnings']:
            self.app.log.warning(' '.join(output['Warnings']))

        return output['Id']

    def __call__(self, container_id: str, cmd_str: str, args: str = "", call: bool = True, cmd_cwd: str = None,
                 msg: str = None, env: dict = None, timeout: int = None, raise_err: bool = False,
                 exit_err: bool = False, user: str = "root", **kwargs) -> CommandData:

        cmd_data = CommandData(f"{cmd_str} {args}" if args else cmd_str)

        if msg and self.app.pargs.verbose:
            self.app.log.info(msg)

        self.app.log.debug(cmd_data.args, self.Meta.label)

        if not call:
            return cmd_data
        
        # TODO: change this to use the environment parameter from exec_create

        cmd = "'"
        if cmd_cwd:
            cmd = f"{cmd} && cd {cmd_cwd}"

        cmd = f"/bin/bash -c {cmd}"

        if timeout:
            cmd = f"timeout --kill-after=1 --signal=SIGTERM {timeout} {cmd}"

        cmd = f"{cmd} {cmd_data.args}'"

        try:
            response = self.app.docker.api.exec_create(container_id, cmd, user=user, tty=False, stdout=True,
                                                       stderr=True, environment=env)
        except APIError:
            raise NexusError(f"failed to create exec object for command: {cmd}")

        exec_id = response['Id']
        self.app.log.debug(f"created exec object with Id {exec_id} for command: {cmd}", self.Meta.label)

        cmd_data.start = datetime.now()
        out = []
        err = []

        for stdout, stderr in self.app.docker.api.exec_start(exec_id, stream=True, demux=True):
            if stdout:
                line = stdout.decode('utf-8').rstrip('\n')

                if self.app.pargs.verbose:
                    print(line)

                out.append(line)

            if stderr:
                err_line = stderr.decode('utf-8').rstrip('\n')

                if self.app.pargs.verbose:
                    print(err_line)

                err.append(err_line)

        cmd_data.end = datetime.now()
        cmd_data.duration = (cmd_data.end - cmd_data.start).total_seconds()
        cmd_data.output = '\n'.join(out)
        cmd_data.error = '\n'.join(err)
        cmd_data.exit_status = self.app.docker.api.exec_inspect(exec_id)['ExitCode']

        if raise_err and cmd_data.error:
            raise CommandError(cmd_data.error)

        if exit_err and cmd_data.error:
            exit(cmd_data.exit_status)

        return cmd_data

    def write_script(self, container: Container, cmd_str: str, path: Path, name: str, mode: oct = 0o777) -> Path:
        bash_file = path / (name + ".sh")
        tar_bash_file = str_to_tarfile(f"#!/bin/bash\n{cmd_str}\n", tar_info_name=bash_file.name)

        with tar_bash_file.open(mode='rb') as fd:
            if not container.put_archive(data=fd, path=str(path)):
                raise NexusError(f'Writing bash file {bash_file.name} to {path} failed.')

        self(container_id=container.id, cmd_str=f"chmod {mode} {bash_file}", raise_err=True)

        return bash_file

    def mkdir(self, container_id: str, path: Path, **kwargs) -> CommandData:
        """
            mkdir wrapper that creates directories on the shared volume.
        """
        return self(container_id=container_id, cmd_str=f"mkdir -p {path}", raise_err=True, **kwargs)

    def write(self, container: Container, data: str, path: Path, name: str, mode: oct = 0o777) -> Path:
        tar_bash_file = str_to_tarfile(data, tar_info_name=name)
        file_path = path / name

        with tar_bash_file.open(mode='rb') as fd:
            if not container.put_archive(data=fd, path=str(path)):
                raise NexusError(f'Writing bash file {name} to {path} failed.')

        self(container_id=container.id, cmd_str=f"chmod {mode} {file_path}", raise_err=True)

        return file_path

    def iterdir(self, container_id: str, path: Path) -> List[Path]:
        cmd_data = self(container_id=container_id, cmd_str=f"ls {path}", raise_err=True)

        return [Path(path, f) for f in cmd_data.output.split('\n')]
