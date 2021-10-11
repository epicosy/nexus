from pathlib import Path
from typing import Union, List

from nexus.core.data.program import Manifest
from nexus.core.data.store import Patch, Signal, ProgramInstance
from nexus.core.database import Instance
from nexus.core.handlers.api import APIHandler
from nexus.core.handlers.container import ContainerHandler


class SynapserHandler(APIHandler, ContainerHandler):
    class Meta:
        label = 'synapser'

    def __init__(self, **kw):
        super(SynapserHandler, self).__init__(**kw)
        self.endpoints = {'repair': f"{self.url_format}/repair",
                          'patches': f"{self.url_format}/patches",
                          'stream': f"{self.url_format}/stream" + "/{rid}"
                          }

    def repair(self, instance: Instance, signals: List[Signal], program_instance: ProgramInstance, manifest: Manifest,
               args: dict):
        return self.post(endpoint_url=self.endpoints['repair'].format(ip=instance.ip, port=instance.port),
                         json={'signals': {signal.arg: signal.command.to_dict() for signal in signals}, 'args': args,
                               'manifest': manifest, 'program_instance': program_instance.to_dict(),
                               'timeout': self.get_timeout()})

    def stream(self, instance: Instance, rid: int):
        return self.get(endpoint_url=self.endpoints['stream'].format(ip=instance.ip, port=instance.port, rid=rid))

    def get_timeout(self):
        if self.app.pargs.timeout:
            return self.app.pargs.timeout

        return self.app.get_config('tool_timeout')

    def get_patches(self, instance: Instance, fixes: bool = False) -> Union[List[Patch], None]:
        response = self.get(endpoint_url=self.endpoints['patches'].format(ip=instance.ip, port=instance.port),
                            json={'fixes': fixes})
        patches = response.json()['patches']

        if patches:
            return [Patch(is_fix=fixes, **patch) for patch in patches]

        return None
