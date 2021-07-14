from cement import Controller, ex
from cement.utils.version import get_version_banner

from ..core.data.store import Task
from ..core.exc import NexusError, CommandError
from ..core.handlers.benchmark import BenchmarkHandler
from ..core.version import get_version

VERSION_BANNER = """
Framework for benchmarking Automatic Program Repair tools %s
%s
""" % (get_version(), get_version_banner())


class Base(Controller):
    class Meta:
        label = 'base'

        # text displayed at the top of --help output
        description = 'Framework for benchmarking Automatic Program Repair tools'

        # text displayed at the bottom of --help output
        epilog = 'Usage: nexus repair --target BitBlaster -wd /tmp/bb'

        # controller level arguments. ex: 'nexus --version'
        arguments = [
            (['-v', '--version'], {'action': 'version', 'version': VERSION_BANNER}),
            (['-vb', '--verbose'], {'help': 'Verbose output.', 'action': 'store_true'})
        ]

    def _default(self):
        """Default action if no sub-command is passed."""
        self.app.log.info(self.app.docker)
        self.app.args.print_help()

    @ex(
        help='Repairs bugs in the program',
        arguments=[
            (["-V", "--vulns"], {'help': "The target vulnerabilities' id", 'nargs': '+'}),
            (["-wd", "--working_dir"], {'help': "Sets the working directory (default: /tmp)", 'type': str}),
            (['-t', '--threads'], {'help': 'Number of threads for running in parallel multiple tasks.', 'type': int}),
            (['-T', '--timeout'], {'help': 'Timeout in seconds for each running task.', 'type': int}),
        ],
    )
    def repair(self):
        try:
            # TODO: define how to choose the tool, benchmark, and task
            benchmark_manager = self.app.handler.get('manager', 'benchmark', setup=True)
            benchmark_handler = benchmark_manager.get(self.app.plugin.get_benchmark('cgcrepair'))
            benchmark_handler.check_programs(self.app.pargs.vulns)
            tasks = [Task(vuln=vuln) for vuln in self.app.pargs.vulns]
            tool = self.app.plugin.get_tool('extractfix')
            tool_handler = self.app.plugin.get_handler(tool)
            task_handler = self.app.plugin.get_handler(self.app.plugin.get_task('extractfix_cgcrepair'))
            runner_handler = self.app.handler.get('runner', 'runner', setup=True)
            runner = runner_handler(tasks, benchmark=benchmark_handler, tool=tool_handler, task=task_handler)
            # TODO: do something with the runner data

        except (CommandError, NexusError) as err:
            self.app.log.error(str(err))

