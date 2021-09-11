from abc import abstractmethod
from pathlib import Path

from cement import Interface
from docker.models.containers import Container

from nexus.core.data.store import Program


class BenchmarkInterface(Interface):
    class Meta:
        interface = 'benchmark'

    @abstractmethod
    def get(self, vid: str, **kwargs) -> Program:
        """
            Returns a local instance of the vulnerability, that is, the working directory with the source code,
            includes, libs, scripts, etc...
        """
        pass

    @abstractmethod
    def get_configs(self):
        """
            Returns all the configurations associated with the benchmark plugin
        """

    @abstractmethod
    def has(self, name: str) -> bool:
        pass

    @abstractmethod
    def load(self, container: Container):
        """
            Loads all vulnerabilities from the associated benchmark plugin
        """

    @abstractmethod
    def prepare(self, program: Program, **kwargs):
        pass

    @abstractmethod
    def prefix(self, program: Program, **kwargs) -> Path:
        """
            Returns the build directory of the program's source files
        """
        pass
