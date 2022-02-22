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
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        orbis_handler = self.app.handler.get('handlers', 'orbis', setup=True)
        benchmarks = container_manager.find_all('benchmark').all()
        table = []

        for instance in benchmarks:
            for vuln in orbis_handler.get_vulns(instance):
                table.append([vuln.id, vuln.cwe, vuln.cve, vuln.pid, instance.name])

        sorted(table, key=lambda x: x[1])
        print(tabulate(table, headers=['Id', 'CWE', 'CVE', 'Program', 'Benchmark']))
