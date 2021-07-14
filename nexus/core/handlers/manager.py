import operator
from cement import Handler

from nexus.core.data.configs import Plugin
from nexus.core.handlers.benchmark import BenchmarkHandler
from nexus.core.interfaces.manager import ManagerInterface


class ToolManager(ManagerInterface, Handler):
    class Meta:
        label = 'tool'

    def get(self):
        docker_handler = self.app.handler.get('handlers', 'docker', setup=True)

        for tool in self.app.plugin.tools:
            tool_handler = self.app.plugin.get_handler(tool)
            if not tool.container:
                tool.container = docker_handler.get_container(tool_handler.get_config('container'))

        return sorted(self.app.plugin.tools, key=operator.attrgetter('name'))


class BenchmarkManager(ManagerInterface, Handler):
    class Meta:
        label = 'benchmark'

    def get(self, benchmark: Plugin) -> BenchmarkHandler:
        docker_handler = self.app.handler.get('handlers', 'docker', setup=True)
        benchmark_handler = self.app.plugin.get_handler(benchmark)

        if not benchmark.container:
            benchmark.container = docker_handler.get_container(benchmark_handler.get_config('container'))

        benchmark_handler.load()

        return benchmark_handler

    def all(self):
        return [self.get(bench) for bench in sorted(self.app.plugin.benchmarks, key=operator.attrgetter('name'))]
