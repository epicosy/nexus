from typing import Union, List

import requests

from nexus.core.data.program import Manifest
from nexus.core.data.store import Patch, Signal, ProgramInstance
from nexus.core.database import Instance
from nexus.core.exc import NexusError
from nexus.core.handlers.api import APIHandler
from nexus.core.handlers.container import ContainerHandler


class SynapserHandler(APIHandler, ContainerHandler):
    class Meta:
        label = 'synapser'

    def __init__(self, **kw):
        super(SynapserHandler, self).__init__(**kw)
        self.endpoints = {'index': self.url_format,
                          'repair': f"{self.url_format}/repair",
                          'patches': f"{self.url_format}/patches",
                          'coverage': f"{self.url_format}/coverage",
                          'stream': f"{self.url_format}/stream" + "/{rid}"
                          }

    def is_running(self, instance: Instance) -> bool:
        try:
            return self.get(endpoint_url=self.endpoints['index'].format(ip=instance.ip, port=instance.port)).ok
        except (requests.exceptions.ConnectionError, NexusError) as ce:
            self.app.log.warning(str(ce))
            return False

    def repair(self, instance: Instance, signals: List[Signal], program_instance: ProgramInstance, manifest: dict,
               args: dict, iid: int):
        return self.post(endpoint_url=self.endpoints['repair'].format(ip=instance.ip, port=instance.port),
                         json_data={'signals': {signal.arg: signal.command.to_json() for signal in signals},
                                    'args': args, 'iid': iid,
                                    'manifest': manifest, 'working_dir': str(program_instance.working_dir),
                                    'build_dir': str(
                                        program_instance.build_dir) if program_instance.build_dir else None,
                                    'timeout': self.get_timeout()})

    def coverage(self, instance: Instance, signals: List[Signal], program_instance: ProgramInstance,
                 manifest: Manifest, iid: int):
        return self.post(endpoint_url=self.endpoints['coverage'].format(ip=instance.ip, port=instance.port),
                         json_data={'signals': {signal.arg: signal.command.to_json() for signal in signals}, 'iid': iid,
                                    'manifest': manifest.to_str(), 'working_dir': str(program_instance.working_dir),
                                    'build_dir': str(
                                        program_instance.build_dir) if program_instance.build_dir else None,
                                    'timeout': self.get_timeout(), })

    def stream(self, instance: Instance, rid: int):
        return self.get(endpoint_url=self.endpoints['stream'].format(ip=instance.ip, port=instance.port, rid=rid))

    def get_timeout(self):
        if self.app.pargs.timeout:
            return self.app.pargs.timeout

        return self.app.get_config('tool_timeout')

    def get_patches(self, instance: Instance, fixes: bool = False) -> Union[List[Patch], None]:
        response = self.get(endpoint_url=self.endpoints['patches'].format(ip=instance.ip, port=instance.port),
                            json_data={'fixes': fixes})
        patches = response.json()['patches']

        if patches:
            return [Patch(is_fix=fixes, **patch) for patch in patches]

        return None
