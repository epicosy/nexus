from tabulate import tabulate
from cement import Controller, ex


class CWE(Controller):
    class Meta:
        label = 'cwe'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help='Lists registered CWE',
        arguments=[
            (['-p', '--program'], {'help': 'Lists vulnerabilities by program', 'nargs': '+'})
        ]
    )
    def list(self):
        benchmark_manager = self.app.handler.get('manager', 'benchmark', setup=True)
        table = []

        for bench in benchmark_manager.all():
            for vuln in bench.all():
                table.append([vuln.id, vuln.cwe, vuln.cve, vuln.program, bench.plugin.name])

        sorted(table, key=lambda x: x[1])
        print(tabulate(table, headers=['Id', 'CWE', 'CVE', 'Program', 'Benchmark']))
