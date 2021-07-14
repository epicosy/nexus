import re
from pathlib import Path
from typing import List, Union

from nexus.core.data.program import Manifest
from nexus.core.data.results import CommandData
from nexus.core.data.store import Program, Patch
from nexus.core.handlers.tool import ToolHandler
from nexus.core.utils.misc import write_bash, match_patches


class GenProg(ToolHandler):
    """GenProg"""
    class Meta:
        label = 'genprog'
        version = 'e720256'

    def setup(self, program: Program, **kwargs):
        """
            Sets the repair tool and writes the bash scripts for running the repair tool
        """
        tool_configs = self.get_configs(args={"--compiler-command": program['compiler-command'],
                                              "--test-command": program['test-command'],
                                              "--program": program['manifest_file'],
                                              "--prefix": program['prefix'],
                                              "--pos-tests": program['pos_tests'],
                                              "--neg-tests": program['neg_tests'],
                                              "--rep": program['rep']})

        run_script = write_bash(cmd=str(tool_configs), name='run', path=program.working_dir)
        program['run_script'] = run_script.name

    def run(self, program: Program, **kwargs) -> CommandData:
        cmd_data = CommandData(args="bash " + program['run_script'])
        command_handler = self.app.handler.get('commands', 'command', setup=True)
        command_handler(cmd_data, cmd_cwd=str(program.working_dir), timeout=self.get_timeout())

        return cmd_data

    def get_patches(self, program: Program, manifest: Manifest, **kwargs) -> List[Patch]:
        patches = []

        for d in program.working_dir.iterdir():
            if d.is_dir() and re.match(r"^\d{6}$", str(d.name)):
                matches = match_patches(sources=manifest.files, program_root_dir=program.working_dir / 'sanity',
                                        patch_root_dir=d)
                patch = self.get_patch(matches=matches, is_fix=False)

                if patch:
                    patches.append(patch)

        return patches

    def get_fix(self, program: Program, manifest: Manifest, **kwargs) -> Union[Patch, None]:
        repair_dir = program.working_dir / Path("repair")

        if repair_dir.exists():
            return None

        matches = match_patches(sources=manifest.files, program_root_dir=program.working_dir / 'sanity',
                                patch_root_dir=repair_dir)

        return self.get_patch(matches=matches, is_fix=True)

    def get_instrumented_files(self, program: Program, manifest: Manifest, **kwargs) -> List[Path]:
        return [program['prefix'] / file for file in manifest.files]


def load(nexus):
    nexus.handler.register(GenProg)
