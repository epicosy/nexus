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


class GenprogCGCRepairTask(TaskHandler):
    class Meta:
        label = 'genprog_cgcrepair'

    def run(self, task: Task, tool: ToolHandler, benchmark: BenchmarkHandler):
        nexus = benchmark.get_nexus()
        program = benchmark.get(task.vuln)

        try:
            task.tests = nexus.get_tests(program)
            manifest = nexus.get_manifest(program)
            manifest.files = [Path(c_to_cpp(str(file))) for file in manifest.files]
            task.add_command(benchmark.prepare(program, raise_err=True))
            program['prefix'] = benchmark.prefix(program, raise_err=True)
            task.add_command(nexus.compile(program, args='--save_temps', raise_err=True))
            inst_files = tool.get_instrumented_files(program, manifest)

            self.add_commands(nexus, program, ' '.join([str(f) for f in inst_files]))

            program['rep'] = "cilpatch" if len(manifest) > 1 else manifest.extensions()[0][1:]
            program['manifest_file'] = manifest.write(program.working_dir)
            program['pos_tests'] = len(task.tests.pos)
            program['neg_tests'] = len(task.tests.neg)

            task.add_command(tool.setup(program, raise_err=True))
            task.add_command(tool.run(program, raise_err=True))
            task.patches = tool.get_patches(program, manifest)
            task.fix = tool.get_fix(program, manifest)
        except (CommandError, NexusError) as err:
            task.error(str(err))
            self.app.log.error(str(err))

    @staticmethod
    def add_commands(nexus: NexusHandler, program: Program, inst_files: str):
        compile_cmd = nexus.compile(program=program, args=f"--fix_files $1 --inst_files {inst_files} --cpp_files --exit_err",
                                    call=False)
        test_cmd = nexus.test(program=program, args=f"--tests $1 --exit_fail", call=False)

        compile_script = nexus.write_script(program, cmd_str=compile_cmd.args, name="compile")
        test_script = nexus.write_script(program, cmd_str=test_cmd.args, name="test")

        program["compiler-command"] = f"\"{compile_script} __SOURCE_NAME__\""
        program["test-command"] = f"\"{test_script} __TEST_NAME__\""


def load(app):
    app.handler.register(GenprogCGCRepairTask)
