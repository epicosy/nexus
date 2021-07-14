from typing import List

from cement import Handler
from cement.core.exc import FrameworkError
from cement.ext.ext_plugin import CementPluginHandler

from nexus.core.exc import NexusError
from nexus.core.data.configs import Plugin


class PluginLoader(CementPluginHandler):
    class Meta:
        label = 'plugin_loader'

    def __init__(self):
        super().__init__()
        self._tools = []
        self._benchmarks = []
        self._tasks = []

    @property
    def tools(self):
        return self._tools

    @property
    def benchmarks(self):
        return self._benchmarks

    @property
    def tasks(self):
        return self._tasks

    def _setup(self, app_obj):
        super()._setup(app_obj)

        self._tools = self.get_plugins('tools')
        self._benchmarks = self.get_plugins('benchmarks')
        self._tasks = self.get_plugins('tasks')

    def get_plugins(self, plugin: str) -> List[Plugin]:
        plugins = []
        for section in self.app.config.get_sections():
            if section.startswith('plugin.' + plugin):
                name = section.split('.')[-1]
                try:
                    self.load_plugin(f"{plugin}.{name}")
                except FrameworkError as fe:
                    raise NexusError(str(fe))
                plugins.append(Plugin(name=name, type=plugin, loaded=f"{plugin}.{name}" in self._loaded_plugins,
                                      enabled='enabled' in self.app.config.keys(section)))

        return plugins

    def get_tool(self, name: str):
        for plugin in self._tools:
            if name == plugin.name:
                return plugin
        return None

    def get_benchmark(self, name: str):
        for plugin in self._benchmarks:
            if name == plugin.name:
                return plugin
        return None

    def get_task(self, name: str):
        for plugin in self._tasks:
            if name == plugin.name:
                return plugin
        return None

    def get_handler(self, plugin: Plugin) -> Handler:
        if not plugin.loaded:
            try:
                self.load_plugin(plugin_name=f"{plugin.type}.{plugin.name}")
                plugin.loaded = True
            except FrameworkError as fe:
                raise NexusError(str(fe))

        handler = self.app.handler.get(plugin.type, plugin.name, setup=True)
        handler.set(plugin)

        return handler
