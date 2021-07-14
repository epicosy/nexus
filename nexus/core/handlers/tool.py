from abc import ABC
from pathlib import Path
from typing import Union, Dict

from cement import Handler
from docker.models.containers import Container

from nexus.core.data.results import CommandData
from nexus.core.data.store import Diff, Patch
from nexus.core.interfaces.tool import ToolInterface
from nexus.core.data.configs import ToolConfigs, Plugin


class ToolHandler(ToolInterface, Handler, ABC):
    class Meta:
        label = 'tool'

    def __init__(self, **kw):
        super(ToolHandler, self).__init__(**kw)
        self.plugin = None

    def set(self, plugin: Plugin):
        self.plugin = plugin

    def get_config(self, key: str):
        return self.app.config.get(self.Meta.label, key)

    def get_configs(self, args: dict = None):
        configs = self.app.config.get_section_dict(self.Meta.label).copy()

        if args:
            if 'args' in configs:
                configs['args'].update(args)
            else:
                configs['args'] = args

        return ToolConfigs(name=self.Meta.label, **configs)

    def get_timeout(self):
        if self.app.pargs.timeout:
            return self.app.pargs.timeout

        return self.app.get_config('tool_timeout')

    def get_container(self) -> Container:
        if not self.plugin.container:
            docker_handler = self.app.handler.get('handlers', 'docker', setup=True)
            self.plugin.container = docker_handler.get_container(self.get_config('container'))

        return self.plugin.container

    def get_diff(self, original: Path, patch: Path) -> Diff:
        command_handler = self.app.handler.get('commands', 'command', setup=True)
        command_handler.log = False
        diff_data = command_handler(CommandData(args=f"diff {original} {patch}"))

        return Diff(source_file=original, patch_file=patch, change=diff_data.output)

    def get_patch(self, matches: Dict[Path, Path], is_fix: bool = False) -> Union[Patch, None]:
        if matches:
            return Patch(is_fix=is_fix, diffs=[self.get_diff(original, patch) for original, patch in matches.items()])
        return None
