from pathlib import Path
from cement import Interface
from abc import abstractmethod
from typing import Dict, Tuple

from nexus.core.data.store import Program, Vulnerability
from nexus.core.data.results import CommandData
from nexus.core.data.program import Tests, Manifest


class NexusInterface(Interface):
    class Meta:
        interface = 'nexus'

    @abstractmethod
    def get_tests(self, program_name: str, **kwargs) -> Tests:
        pass

    @abstractmethod
    def get_manifest(self, program_name: str, **kwargs) -> Manifest:
        pass

    @abstractmethod
    def get_programs(self, **kwargs):
        """Gets the benchmark's programs"""
        pass

    @abstractmethod
    def get_vulns(self, **kwargs) -> Dict[str, Vulnerability]:
        """Gets all the benchmark's vulnerabilities"""
        pass

    @abstractmethod
    def checkout(self, program: Program, **kwargs) -> CommandData:
        """Checks out the program to the working directory"""
        pass

    @abstractmethod
    def make(self, program: Program, **kwargs) -> CommandData:
        pass

    @abstractmethod
    def compile(self, program: Program, **kwargs) -> CommandData:
        pass

    @abstractmethod
    def test(self, program: Program, **kwargs) -> CommandData:
        pass

    @abstractmethod
    def patch(self, program: Program, source: Path, patch: Path, **kwargs):
        """
            Applies file patches to the program under repair
            source: the source file to patch
            patch: the patch file (including the full path)
        """
        pass
