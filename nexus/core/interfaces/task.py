from abc import abstractmethod
from cement import Interface

from nexus.core.data.store import Task
from nexus.core.handlers.benchmark import BenchmarkHandler
from nexus.core.handlers.tool import ToolHandler


class TaskInterface(Interface):
    class Meta:
        interface = 'tasks'

    @abstractmethod
    def get_config(self, key: str):
        pass

    @abstractmethod
    def run(self, task_data: Task, benchmark: BenchmarkHandler, tool: ToolHandler):
        pass
