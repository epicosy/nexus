from abc import abstractmethod
from pathlib import Path
from typing import List

from cement import Interface
from docker.models.containers import Container

from nexus.core.data.program import Manifest
from nexus.core.data.store import Program
from nexus.core.data.store import Patch
from nexus.core.handlers.nexus import NexusHandler


class ToolInterface(Interface):
    class Meta:
        interface = 'tools'

    @abstractmethod
    def get_container(self) -> Container:
        pass

    @abstractmethod
    def get_config(self, key: str):
        pass

    @abstractmethod
    def get_configs(self):
        pass

    @abstractmethod
    def setup(self, program: Program, nexus: NexusHandler, **kwargs):
        pass

    @abstractmethod
    def run(self, program: Program, **kwargs):
        pass

    @abstractmethod
    def get_instrumented_files(self, program: Program, manifest: Manifest, **kwargs) -> List[Path]:
        """
            Returns the instrumented files by the program, if any
        """
        pass

    @abstractmethod
    def get_patches(self, program: Program, manifest: Manifest, **kwargs) -> List[Patch]:
        pass

    @abstractmethod
    def get_fix(self, program: Program, manifest: Manifest, **kwargs) -> List[Patch]:
        pass
