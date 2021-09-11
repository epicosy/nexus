from cement import Interface
from abc import abstractmethod

from nexus.core.data.context import Context
from nexus.core.data.store import Task


class NexusInterface(Interface):
    class Meta:
        interface = 'nexus'

    @abstractmethod
    def get_config(self, key: str):
        pass

    @abstractmethod
    def run(self, task_data: Task, context: Context):
        pass
