from pathlib import Path
from typing import Union, List

from nexus.core.data.store import Patch
from nexus.core.database import Instance
from nexus.core.handlers.api import APIHandler
from nexus.core.handlers.container import ContainerHandler


class SynapserHandler(APIHandler, ContainerHandler):
    class Meta:
        label = 'synapser'

    def __init__(self, **kw):
        super(SynapserHandler, self).__init__(**kw)
        self.endpoints = {'repair': f"{self.url_format}/repair",
                          'patches': f"{self.url_format}/patches"
                          }

    def repair(self, instance: Instance, signals: dict, args: dict, working_dir: Path):
        return self.post(endpoint_url=self.endpoints['repair'].format(ip=instance.ip, port=instance.port),
                         json={'signals': signals, 'timeout': self.get_timeout(), 'working_dir': str(working_dir),
                               'args': args})

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
