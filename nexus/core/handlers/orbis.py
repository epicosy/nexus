import requests

from binascii import b2a_hex
from os import urandom
from pathlib import Path
from typing import Tuple, Dict, Any

from nexus.core.data.program import Manifest
from nexus.core.data.results import CommandData
from nexus.core.data.store import Vulnerability, Program, Tests
from nexus.core.database import Instance
from nexus.core.exc import NexusError
from nexus.core.handlers.api import APIHandler


class OrbisHandler(APIHandler):
    class Meta:
        label = 'orbis'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.endpoints = {
            'compile': f"{self.url_format}/compile",
            'checkout': f"{self.url_format}/checkout",
            'make': f"{self.url_format}/make",
            'test': f"{self.url_format}/test",
            'program': f"{self.url_format}/program" + "/{pid}",
            'programs': f"{self.url_format}/programs",
            'vuln': f"{self.url_format}/vuln" + "/{vid}",
            'vulns': f"{self.url_format}/vulns",
        }

    # TODO: connect to a volume
    def get_working_dir(self, program_name: str, randomize: bool = False) -> Path:
        container_handler = self.app.handler.get('manager', 'benchmark', setup=True)
        instance = container_handler.get_instance(self.Meta.label)
        working_dir = Path(f"/{instance.volume}", program_name)

        if randomize:
            working_dir = working_dir.parent / (working_dir.name + "_" + b2a_hex(urandom(2)).decode())

        return Path(working_dir)

    def get_manifest(self, instance: Instance, pid: str) -> Dict[str, Any]:
        response = requests.get(f"{instance.endpoint}/manifest/{pid}")

        if response.status_code != 200:
            raise NexusError('Get manifest failed')

        return response.json()['manifest']

    def get_program(self, instance: Instance, pid: str, args: dict = None) -> Program:
        response = self.get(endpoint_url=self.endpoints['program'].format(ip=instance.ip, port=instance.port, pid=pid),
                            json=args)
        response_json = response.json()
        response_json['vuln']['pid'] = pid
        tests = Tests(**response_json['tests'])
        manifest = Manifest(response_json['manifest'])
        response_json['vuln']['program'] = response_json['name']
        vuln = Vulnerability(**response_json['vuln'])
        del response_json['vuln']
        del response_json['tests']
        del response_json['manifest']

        return Program(**response_json, manifest=manifest, vuln=vuln, tests=tests)

    def get_programs(self, instance: Instance, **kwargs):
        return self.get(endpoint_url=self.endpoints['programs'].format(ip=instance.ip, port=instance.port),
                        json=kwargs).json()

    def get_vuln(self, instance: Instance, vid: str, args: dict = None) -> Vulnerability:
        response = self.get(endpoint_url=self.endpoints['vuln'].format(ip=instance.ip, port=instance.port, vid=vid),
                            json=args)
        return Vulnerability(**response.json())

    def get_vulns(self, instance: Instance, args: dict = None):
        response = self.get(endpoint_url=self.endpoints['vulns'].format(ip=instance.ip, port=instance.port), json=args)
        return [Vulnerability(**vuln) for vuln in response.json().values()]

    def checkout(self, instance: Instance, args: dict) -> Tuple[int, Path]:
        response = self.post(endpoint_url=self.endpoints['checkout'].format(ip=instance.ip, port=instance.port),
                             json=args).json()

        return response['iid'], Path(response['working_dir'])

    def make(self, instance: Instance, args: dict) -> CommandData:
        return self.post(endpoint_url=self.endpoints['make'].format(ip=instance.ip, port=instance.port),
                         json=args).json()

    def url(self, endpoint: str, instance: Instance) -> Dict[str, Any]:
        return self.endpoints[endpoint].format(ip=instance.ip, port=instance.port)

    def compile(self, instance: Instance, args: dict) -> Tuple[int, Path]:
        response = self.post(endpoint_url=self.endpoints['compile'].format(ip=instance.ip, port=instance.port),
                             json=args).json()

        return response['iid'], Path(response['build'])

    def test(self, instance: Instance, iid: str, args: dict) -> CommandData:
        return self.post(endpoint_url=self.endpoints['test'].format(ip=instance.ip, port=instance.port),
                         json=args).json()

    def patch(self, instance: Instance, args: dict):
        # 'source': source, 'patch': patch
        return self.post(endpoint_url=self.endpoints['patch'].format(ip=instance.ip, port=instance.port),
                         json=args).json()
