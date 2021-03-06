from cement import App, TestApp
from cement.core.exc import CaughtSignal

from nexus.controllers.benchmark import Benchmark
from nexus.controllers.cwe import CWE
from nexus.controllers.database import Database
from nexus.controllers.tool import Tool
from .core.exc import NexusError
from .controllers.base import Base

# Handlers
from nexus.core.handlers.base import CoreHandler
from nexus.core.handlers.plugin import PluginLoader
from nexus.core.handlers.runner import RunnerHandler
from nexus.core.handlers.container import ContainerHandler
from nexus.core.handlers.command import CommandHandler
from nexus.core.handlers.manager import NexusManager, ContainerManager
from nexus.core.handlers.synapser import SynapserHandler
from nexus.core.handlers.orbis import OrbisHandler

# Interfaces
from nexus.core.interfaces.base import CoreInterface
from nexus.core.interfaces.tool import ToolInterface
from nexus.core.interfaces.nexus import NexusInterface
from nexus.core.interfaces.runner import RunnerInterface
from nexus.core.interfaces.manager import ManagersInterface
from nexus.core.interfaces.command import CommandInterface
from nexus.core.interfaces.database import DatabaseInterface
from nexus.core.interfaces.handlers import HandlersInterface
from nexus.core.interfaces.benchmark import BenchmarkInterface


class Nexus(App):
    """Nexus primary application."""

    class Meta:
        label = 'nexus'

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'nexus.core.hooks.docker',
            'nexus.core.hooks.database',
            'yaml',
            'colorlog',
            'jinja2',
        ]

        # configuration handler
        config_handler = 'yaml'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'

        plugin_handler = 'plugin_loader'

        # register interfaces
        interfaces = [
            NexusInterface, CoreInterface, ToolInterface, BenchmarkInterface, RunnerInterface,
            CommandInterface, HandlersInterface, ManagersInterface, DatabaseInterface
        ]

        # register handlers
        handlers = [
            Base, Tool, Benchmark, CWE, Database, RunnerHandler, CoreHandler, CommandHandler, PluginLoader,
            ContainerHandler, ContainerManager, ContainerHandler, NexusManager, SynapserHandler, OrbisHandler
        ]

    def get_config(self, key: str):
        if self.config.has_section(self.Meta.label):
            if key in self.config.keys(self.Meta.label):
                return self.config.get(self.Meta.label, key)

        return None

    def get_section(self, name: str):
        return self.config.get_section_dict(name).copy()


class NexusTest(TestApp, Nexus):
    """A sub-class of Nexus that is better suited for testing."""

    class Meta:
        label = 'nexus'


def main():
    with Nexus() as app:
        try:
            # TODO: tool_configs.validate()
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except NexusError as e:
            print('NexusError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
