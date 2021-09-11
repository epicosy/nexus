from abc import ABC
from typing import List

from cement import Handler

from nexus.core.data.configs import Plugin
from nexus.core.interfaces.nexus import NexusInterface


class NexusHandler(NexusInterface, Handler, ABC):
    class Meta:
        label = 'nexus'

    def __init__(self, tool: str, benchmark: str, **kw):
        super(NexusHandler, self).__init__(**kw)
        self.plugin = None
        self._tool = tool
        self._benchmark = benchmark

    # def get(self, tbp_id: int) -> NexusData:
    #    return self.app.db.query(NexusData, tbp_id)
    '''
    def all(self) -> List[NexusData]:
        return self.app.db.query(NexusData)

    def get(self) -> NexusData:
        return self.app.db.filter(NexusData, {NexusData.name: lambda tbp_name: tbp_name == self.Meta.label}).first()

    def add(self, tool_id: int, benchmark_id: int, status: str = "created") -> int:
        return self.app.db.add(NexusData(tid=tool_id, bid=benchmark_id, name=self.Meta.label, status=status))
    '''
    def set(self, plugin: Plugin):
        self.plugin = plugin

    def get_config(self, key: str):
        return self.app.config.get(self.Meta.label, key)

    def get_configs(self):
        return self.app.config.get_section_dict(self.Meta.label).copy()

    @property
    def tool(self):
        return self._tool

    @property
    def benchmark(self):
        return self._benchmark

    def tool_configs(self):
        return self.app.get_section(self.tool)

    def benchmark_configs(self):
        return self.app.get_section(self.benchmark)
