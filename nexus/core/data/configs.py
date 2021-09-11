from dataclasses import dataclass, field
from pathlib import Path

from nexus.core.utils.misc import args_to_str


@dataclass
class Plugin:
    name: str
    loaded: bool
    enabled: bool


@dataclass
class Configs:
    name: str

    def __str__(self):
        return self.name


@dataclass
class ToolConfigs(Configs):
    program: str
    path: str
    docker: dict
    args: dict = field(default_factory=lambda: {})
    sanity_check: bool = False
    fault_localization: bool = False

    def add_arg(self, opt: str, arg):
        self.args[opt] = arg

    def validate(self):
        assert Path(self.path).exists(), "Parent path to the executable program not found"
        assert Path(self.path, self.program).exists(), "Executable program for the repair tool not found"

    def __str__(self):
        return f"{self.path}/{self.program} {args_to_str(self.args)}"
