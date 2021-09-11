from cement.core.exc import FrameworkError
from cement.ext.ext_plugin import CementPluginHandler

from nexus.core.exc import NexusError
from nexus.core.data.configs import Plugin


class PluginLoader(CementPluginHandler):
    class Meta:
        label = 'plugin_loader'

    def __init__(self):
        super().__init__()
        self._nexuses = {}

    def get(self, name: str):
        return self._nexuses[name]

    @property
    def nexuses(self):
        return self._nexuses

    def __setitem__(self, name: str, plugin: Plugin):
        self._nexuses[name] = plugin

    def _setup(self, app_obj):
        super()._setup(app_obj)

        for section in self.app.config.get_sections():
            try:
                _, kind, name = section.split('.')

                if kind != 'nexus':
                    continue

                try:
                    self.load_plugin(f"{kind}.{name}")
                except FrameworkError as fe:
                    raise NexusError(str(fe))
                loaded = f"{kind}.{name}" in self._loaded_plugins
                enabled = 'enabled' in self.app.config.keys(section)
                self._nexuses[name] = Plugin(name=name, loaded=loaded, enabled=enabled)
            except ValueError:
                continue

    def has(self, name: str):
        return name in self._nexuses
