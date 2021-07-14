from tabulate import tabulate
from cement import Controller, ex


class Benchmarks(Controller):
    class Meta:
        label = 'benchmarks'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help='Lists registered benchmarks'
    )
    def list(self):
        benchmark_manager = self.app.handler.get('manager', 'benchmark', setup=True)
        table = []

        for benchmark in benchmark_manager.get():
            table.append([benchmark.name, benchmark.enabled, benchmark.loaded, benchmark.container.id if benchmark.container else '-'])

        print(tabulate(table, headers=['Benchmark', 'Enabled', 'Loaded', 'Container']))
