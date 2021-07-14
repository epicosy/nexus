import re
from pathlib import Path
from typing import List, Union

from nexus.core.data.program import Manifest
from nexus.core.data.results import CommandData
from nexus.core.data.store import Program, Patch
from nexus.core.handlers.nexus import NexusHandler
from nexus.core.handlers.tool import ToolHandler
from nexus.core.utils.misc import write_bash, match_patches


class ExtractFix(ToolHandler):
    """ExtractFix"""
    class Meta:
        label = 'extractfix'
        version = ''

    def setup(self, program: Program, nexus: NexusHandler, **kwargs):
        """
            Sets the repair tool and writes the bash scripts for running the repair tool
        """
        tool_configs = self.get_configs(args={"--source_path": program['source_path'],
                                              "--tests": program['tests'],
                                              "--run-command": program['run-command'],
                                              "--bug_type": program['bug_type'],
                                              "--binary_name": program['binary_name']})

        run_script = write_bash(cmd=str(tool_configs), name='run', path=program.working_dir)
        program['run_script'] = run_script.name

    def run(self, program: Program, **kwargs) -> CommandData:
        cmd_data = CommandData(args="/data/casino/run.sh")
        # TODO: wrap this around in some method
        container = self.get_container()
        docker_handler = self.app.handler.get('handlers', 'docker', setup=True)
        docker_handler.command(container, cmd_data, msg='running ExtractFix', timeout=self.get_timeout(),
                               raise_err=True, env=Path("/ExtractFix/setup.sh"))
        return cmd_data

    def get_patches(self, program: Program, manifest: Manifest, **kwargs) -> List[Patch]:
        patches = []

        for d in program.working_dir.iterdir():
            if d.is_dir() and re.match(r"^result\d{1,3}$", str(d.name)):
                # TODO: workaround this -> name of the patch file not the same as the name of the target file
                matches = match_patches(sources=manifest.files, program_root_dir=program.working_dir / 'sanity',
                                        patch_root_dir=d)
                patch = self.get_patch(matches=matches, is_fix=False)

                if patch:
                    patches.append(patch)

        return patches

    def get_fix(self, program: Program, manifest: Manifest, **kwargs) -> Union[Patch, None]:
        pass

    def get_instrumented_files(self, program: Program, manifest: Manifest, **kwargs) -> List[Path]:
        pass


def load(nexus):
    nexus.handler.register(ExtractFix)
