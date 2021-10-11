from cement import Interface
from abc import abstractmethod

from nexus.core.data.context import Context
from nexus.core.data.store import Program, Vulnerability


class NexusInterface(Interface):
    class Meta:
        interface = 'nexus'

    @abstractmethod
    def get_config(self, key: str):
        pass

    @abstractmethod
    def run(self, program: Program, vulnerability: Vulnerability, context: Context):
        pass
