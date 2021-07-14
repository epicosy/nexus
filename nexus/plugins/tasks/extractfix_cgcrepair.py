import re
from pathlib import Path

from nexus.core.data.store import Task
from nexus.core.data.store import Program
from nexus.core.exc import CommandError, NexusError
from nexus.core.handlers.nexus import NexusHandler
from nexus.core.handlers.task import TaskHandler
from nexus.core.handlers.benchmark import BenchmarkHandler
from nexus.core.handlers.tool import ToolHandler


def c_to_cpp(c_file: str):
    if '.cc' in c_file:
        return re.sub(r'.cc$', '.ii', c_file)
    return re.sub(r'.c$', '.i', c_file)


class ExtractFixCGCRepairTask(TaskHandler):
    class Meta:
        label = 'extractfix_cgcrepair'

    def run(self, task: Task, tool: ToolHandler, benchmark: BenchmarkHandler):
        nexus = benchmark.get_nexus()
        program = benchmark.get(task.vuln)

        try:
            tool_container = tool.get_container()
            manifest = nexus.get_manifest(program)
            nexus.mkdir(path=program.working_dir, container=tool_container)
            nexus.mkdir(path=program.working_dir / 'project', container=tool_container)

            program['source_path'] = program.working_dir
            program['tests'] = nexus.write_script(container=tool_container, cmd_str=self.test_script(program, nexus),
                                                  path=program.working_dir, name='test')
            program['run-command'] = nexus.write_script(container=tool_container, name='project_build',
                                                        cmd_str=self.build_script(program, nexus),
                                                        path=program.working_dir)
            program['bug_type'] = self.get_bug_type(program)
            program['binary_name'] = manifest.files[0].stem
            program['config_script'] = nexus.write_script(container=tool_container,  name='project_config',
                                                          cmd_str=self.config_script(program, nexus),
                                                          path=program.working_dir)
            program['compile_script'] = nexus.write_script(container=tool_container, name='project_compile',
                                                           cmd_str=self.compile_script(program, nexus),
                                                           path=program.working_dir)
            task.add_command(tool.setup(program, nexus))
            task.add_command(tool.run(program, raise_err=True))
            task.patches = tool.get_patches(program, manifest)
            task.fix = tool.get_fix(program, manifest)
        except (CommandError, NexusError) as err:
            task.error(str(err))
            self.app.log.error(str(err))

    def config_script(self, program, nexus):
        # TODO: implement this
        pass

    def build_script(self, program, nexus):
        # TODO: implement this
        pass

    def compile_script(self, program, nexus):
        # TODO: implement this
        pass

    def test_script(self, program, nexus):
        # TODO: implement this
        pass

    def get_bug_type(self, program) -> str:
        # TODO: implement this
        pass


def load(app):
    app.handler.register(ExtractFixCGCRepairTask)
