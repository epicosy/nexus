from abc import ABC
from binascii import b2a_hex
from os import urandom
from pathlib import Path
from typing import List, AnyStr

from nexus.core.data.configs import Plugin
from nexus.core.data.results import CommandData
from nexus.core.data.store import Vulnerability
from nexus.core.exc import NexusError
from nexus.core.interfaces.benchmark import BenchmarkInterface
from nexus.core.handlers.nexus import LocalNexus
from nexus.core.handlers.nexus import RemoteNexus
from cement import Handler


class BenchmarkHandler(BenchmarkInterface, Handler, ABC):
    class Meta:
        label = 'benchmark'

    def __init__(self, local_nexus: str, remote_nexus: str, **kwargs):
        super().__init__(**kwargs)
        self.vulns = {}
        self.plugin = None
        self.local_nexus = local_nexus
        self.remote_nexus = remote_nexus

    def set(self, plugin: Plugin):
        self.plugin = plugin

    def __call__(self, *args, **kwargs) -> CommandData:
        return self.get_nexus()(**kwargs)

    def get_config(self, key: str):
        return self.app.config.get(self.Meta.label, key)

    def get_configs(self):
        return self.app.config.get_section_dict(self.Meta.label).copy()

    # TODO: connect to a volume
    def get_working_dir(self, program_name: str, randomize: bool = False) -> Path:
        root_dir = self.app.pargs.working_dir if self.app.pargs.working_dir else self.app.get_config('working_dir')
        working_dir = Path(root_dir, program_name)

        if randomize:
            working_dir = working_dir.parent / (working_dir.name + "_" + b2a_hex(urandom(2)).decode())

        return Path(working_dir)

    def check_programs(self, names: List[AnyStr]):
        if names:
            for name in names:
                if not self.has(name):
                    raise NexusError(f"One of the programs specified not found")
        else:
            self.app.pargs.vid = list(self.vulns.keys())

    def has(self, name: str) -> bool:
        return name in self.vulns

    def all(self) -> List[Vulnerability]:
        return list(self.vulns.values())

    def get_local_nexus(self) -> LocalNexus:
        return self.app.handler.get('nexus', self.local_nexus, setup=True)

    def get_remote_nexus(self) -> RemoteNexus:
        return self.app.handler.get('nexus', self.remote_nexus, setup=True)

    def get_nexus(self):
        if 'remote' in self.get_config('handler'):
            return self.get_remote_nexus()

        return self.get_local_nexus()
