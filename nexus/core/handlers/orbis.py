import requests

from binascii import b2a_hex
from os import urandom
from pathlib import Path

from nexus.core.data.results import CommandData
from nexus.core.data.store import Vulnerability, Program, ProgramInstance
from nexus.core.database import Instance
from nexus.core.exc import NexusError
from nexus.core.handlers.api import APIHandler


class OrbisHandler(APIHandler):
    class Meta:
        label = 'orbis'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.endpoints = {
            'index': self.url_format,
            'build': f"{self.url_format}/build",
            'checkout': f"{self.url_format}/checkout",
            'make': f"{self.url_format}/make",
            'test': f"{self.url_format}/test",
            'program': f"{self.url_format}/project" + "/{pid}",
            'programs': f"{self.url_format}/projects",
            'instance': f"{self.url_format}/instance" + "/{iid}",
            'instances': f"{self.url_format}/instances",
            'vuln': f"{self.url_format}/vuln" + "/{vid}",
            'vulns': f"{self.url_format}/vulns",
        }

    def is_running(self, instance: Instance) -> bool:
        try:
            return self.get(endpoint_url=self.endpoints['index'].format(ip=instance.ip, port=instance.port)).ok
        except (requests.exceptions.ConnectionError, NexusError) as ce:
            self.app.log.warning(str(ce))
            return False

    # TODO: connect to a volume
    def get_working_dir(self, program_name: str, randomize: bool = False) -> Path:
        container_handler = self.app.handler.get('manager', 'benchmark', setup=True)
        instance = container_handler.get_instance(self.Meta.label)
        working_dir = Path(f"/{instance.volume}", program_name)

        if randomize:
            working_dir = working_dir.parent / (working_dir.name + "_" + b2a_hex(urandom(2)).decode())

        return Path(working_dir)

    def get_instance(self, instance: Instance, iid: str) -> Program:
        response = self.get(endpoint_url=self.endpoints['instance'].format(ip=instance.ip, port=instance.port, iid=iid))

        return response.json()

    def get_instances(self, instance: Instance, **kwargs):
        return self.get(endpoint_url=self.endpoints['instances'].format(ip=instance.ip, port=instance.port),
                        json_data=kwargs).json()

    def get_program(self, instance: Instance, pid: str, args: dict = None) -> Program:
        response = self.get(endpoint_url=self.endpoints['program'].format(ip=instance.ip, port=instance.port, pid=pid),
                            json_data=args)

        pid, program = next(iter(response.json().items()))

        return Program(id=pid, **program)

    def get_programs(self, instance: Instance, **kwargs):
        return self.get(endpoint_url=self.endpoints['programs'].format(ip=instance.ip, port=instance.port),
                        json_data=kwargs).json()

    def get_vuln(self, instance: Instance, vid: str, args: dict = None) -> Vulnerability:
        response = self.get(endpoint_url=self.endpoints['vuln'].format(ip=instance.ip, port=instance.port, vid=vid),
                            json_data=args)

        vid, vuln = next(iter(response.json().items()))

        return Vulnerability(id=vid, **vuln)

    def get_vulns(self, instance: Instance, args: dict = None):
        response = self.get(endpoint_url=self.endpoints['vulns'].format(ip=instance.ip, port=instance.port), json=args)
        return [Vulnerability(**vuln) for vuln in response.json().values()]

    def checkout(self, instance: Instance, vuln: Vulnerability, working_dir: Path = None,
                 args: dict = None) -> ProgramInstance:
        json_data = {'vid': vuln.id, 'root_dir': f"/{instance.volume}"}

        if working_dir:
            json_data['working_dir'] = str(working_dir)

        if args:
            json_data['args'] = args

        response = self.post(endpoint_url=self.endpoints['checkout'].format(ip=instance.ip, port=instance.port),
                             json_data=json_data).json()

        return ProgramInstance(iid=response['iid'], working_dir=Path(response['working_dir']))

    def make(self, instance: Instance, args: dict) -> CommandData:
        return self.post(endpoint_url=self.endpoints['make'].format(ip=instance.ip, port=instance.port),
                         json_data=args).json()

    def url(self, action: str, instance: Instance) -> str:
        return self.endpoints[action].format(ip=instance.ip, port=instance.port)

    def build(self, instance: Instance, program_instance: ProgramInstance, args: dict) -> ProgramInstance:
        json_data = {'iid': program_instance.iid}

        if args:
            json_data['args'] = args

        response = self.post(endpoint_url=self.endpoints['build'].format(ip=instance.ip, port=instance.port),
                             json_data=json_data).json()
        print(response)
        program_instance.build_dir = Path(response['returns']['build'])
        program_instance.build_args = response['returns'].get('build_args', {})

        return program_instance

    def test(self, instance: Instance, program_instance: ProgramInstance, args: dict) -> CommandData:
        return self.post(endpoint_url=self.endpoints['test'].format(ip=instance.ip, port=instance.port),
                         json_data=args).json()

    def patch(self, instance: Instance, args: dict):
        # 'source': source, 'patch': patch
        return self.post(endpoint_url=self.endpoints['patch'].format(ip=instance.ip, port=instance.port),
                         json_data=args).json()
