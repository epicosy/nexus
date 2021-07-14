from nexus.core.interfaces.base import CoreInterface
from cement import Handler


class CoreHandler(CoreInterface, Handler):
    class Meta:
        label = 'core'

    def get_config(self, section: str, key: str):
        if self.app.config.has_section(section):
            if key in self.app.config.keys(key):
                return self.app.config.get(section, key)
        return None

    def get_configs(self, section: str):
        self.app.config.get_section_dict(section).copy()
