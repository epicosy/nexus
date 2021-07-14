from cement import Interface
from abc import abstractmethod


class CoreInterface(Interface):
    class Meta:
        interface = 'core'

    @abstractmethod
    def get_config(self, section: str, key: str):
        pass

    @abstractmethod
    def get_configs(self, section: str):
        pass
