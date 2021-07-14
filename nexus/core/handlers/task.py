from abc import ABC

from cement import Handler

from nexus.core.data.configs import Plugin
from nexus.core.interfaces.task import TaskInterface


class TaskHandler(TaskInterface, Handler, ABC):
    class Meta:
        label = 'task'

    def __init__(self, **kw):
        super(TaskHandler, self).__init__(**kw)
        self.plugin = None

    def set(self, plugin: Plugin):
        self.plugin = plugin

    def get_config(self, key: str):
        return self.app.config.get(self.Meta.label, key)

    def get_configs(self):
        return self.app.config.get_section_dict(self.Meta.label).copy()

    def get_tool(self, name: str):
        return self.app.handler.get('tool', name, setup=True)

    def get_benchmark(self, name: str):
        return self.app.handler.get('benchmark', name, setup=True)
