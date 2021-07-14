from datetime import datetime
from pathlib import Path

from cement import Handler
from docker.errors import NotFound
from docker.errors import APIError
from docker.models.containers import Container

from nexus.core.data.results import CommandData
from nexus.core.exc import NexusError, CommandError
from nexus.core.interfaces.handlers import HandlersInterface


class DockerHandler(HandlersInterface, Handler):
    class Meta:
        label = 'docker'

    def get_container(self, name: str):
        try:
            return self.app.docker.containers.get(name)
        except NotFound as nf:
            self.app.log.error(str(nf))

            return None

    def command(self, container: Container, cmd_data: CommandData, cmd_cwd: str = None, msg: str = None, env: Path = None,
                timeout: int = None, raise_err: bool = False, exit_err: bool = False, **kwargs) -> CommandData:

        if msg and self.app.pargs.verbose:
            self.app.log.info(msg)

        self.app.log.debug(cmd_data.args)

        cmd = f"'source {env} &&" if env else "'"
        if cmd_cwd:
            cmd = f"{cmd} && cd {cmd_cwd}"

        cmd = f"/bin/bash -c {cmd}"

        if timeout:
            cmd = f"timeout --kill-after=1 --signal=SIGTERM {timeout} {cmd}"

        cmd = f"{cmd} {cmd_data.args}'"

        try:
            response = self.app.docker.api.exec_create(container.id, cmd, tty=True, stdout=True, stderr=True)
        except APIError:
            raise NexusError(f"failed to create exec object for command: {cmd}")

        exec_id = response['Id']
        self.app.log.debug(f"created exec object with Id {exec_id} for command: {cmd}")

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
        cmd_data.duration = (cmd_data.start - cmd_data.end).total_seconds()
        cmd_data.output = '\n'.join(out)
        cmd_data.error = '\n'.join(err)
        cmd_data.exit_status = self.app.docker.api.exec_inspect(exec_id)['ExitCode']

        if raise_err and cmd_data.error:
            raise CommandError(cmd_data.error)

        if exit_err and cmd_data.error:
            exit(cmd_data.exit_status)

        return cmd_data

    def mkdir(self,  container: Container, path: Path, **kwargs) -> CommandData:
        """
            mkdir wrapper that creates directories on the shared volume.
        """
        return self.command(container=container, cmd_data=CommandData(args=f"mkdir -p {path}"), raise_err=True, **kwargs)

    def write_script(self, container: Container, cmd_str: str, path: Path, name: str, mode: oct = 0o777) -> Path:
        bash_file = path / (name + ".sh")
        container.put_archive(data=str.encode(f"#!/bin/bash\n{cmd_str}"), path=str(bash_file))
        self.command(container=container, cmd_data=CommandData(args=f"chmod {mode} {bash_file}"), raise_err=True)

        return bash_file
