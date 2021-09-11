from abc import abstractmethod
from pathlib import Path
from typing import List

from cement import Interface

from nexus.core.data.program import Manifest
from nexus.core.data.store import Program
from nexus.core.data.store import Patch


class ToolInterface(Interface):
    class Meta:
        interface = 'tool'

    @abstractmethod
    def get_configs(self):
        pass

    @abstractmethod
    def setup(self, program: Program, **kwargs):
        pass

    @abstractmethod
    def run(self, program: Program, **kwargs):
        pass

    @abstractmethod
    def get_patches(self, program: Program, manifest: Manifest, **kwargs) -> List[Patch]:
        pass

    @abstractmethod
    def get_fix(self, program: Program, manifest: Manifest, **kwargs) -> List[Patch]:
        pass
