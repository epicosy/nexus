from tabulate import tabulate

from cement import Controller, ex
from cement.utils.version import get_version_banner
from cement.utils.version import get_version

from ..core.data.store import Task
from ..core.exc import NexusError, CommandError

# TODO: should be dynamic
VERSION = (0, 0, 1, 'alpha', 0)
VERSION_BANNER = """
Framework for benchmarking Automatic Program Repair tools %s
%s
""" % (get_version(VERSION), get_version_banner())


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
            (['-t', '--threads'], {'help': 'Number of threads for running in parallel multiple tasks.', 'type': int}),
            (['-T', '--timeout'], {'help': 'Timeout in seconds for each running task.', 'type': int, 'default': 3600}),
            (["-N", "--name"], {'help': "The name of the target Nexus", 'type': str, 'required': True})
        ],
    )
    def repair(self):
        try:
            if not self.app.plugin.has(self.app.pargs.name):
                self.app.log.error(f"Nexus {self.app.pargs.name} not found. Make sure the nexus's plugin is registered.")
                exit(1)

            nexus_handler = self.app.handler.get('nexus', self.app.pargs.name, setup=True)
            nexus_manager = self.app.handler.get('managers', 'nexus', setup=True)
            context = nexus_manager.get_context(nexus_handler)
            orbis_handler = self.app.handler.get('handlers', 'orbis', setup=True)

            if self.app.pargs.vulns:
                vulns = [orbis_handler.get_vuln(context.benchmark.instance, vuln) for vuln in self.app.pargs.vulns]
            else:
                vulns = orbis_handler.get_vulns(context.benchmark.instance)

            tasks = [Task(program=orbis_handler.get_program(context.benchmark.instance, vuln.pid), vulnerability=vuln) for vuln in vulns]

            runner_handler = self.app.handler.get('runner', 'runner', setup=True)
            runner_data = runner_handler(tasks, context=context, nexus_handler=nexus_handler)

        except (CommandError, NexusError) as err:
            self.app.log.error(str(err))

    @ex(
        help='Lists installed nexuses'
    )
    def list(self):
        table = []

        for name, plugin in sorted(self.app.plugin.nexuses.items()):
            nexus_handler = self.app.handler.get('nexus', name, setup=True)
            table.append([name, plugin.enabled, plugin.loaded, nexus_handler.benchmark, nexus_handler.tool])

        print(tabulate(table, headers=['Nexus', 'Enabled', 'Loaded', 'Benchmark', 'Tool']))
