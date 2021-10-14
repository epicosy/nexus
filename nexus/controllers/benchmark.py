from docker.errors import APIError
from tabulate import tabulate
from cement import Controller, ex

from nexus.core.database import Instance


class Benchmark(Controller):
    class Meta:
        label = 'benchmark'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help='Lists registered benchmarks'
    )
    def list(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        benchmarks = container_manager.find_all('benchmark')
        table = []

        for benchmark in benchmarks:
            table.append([benchmark.name, benchmark.id, benchmark.status, benchmark.ip, benchmark.port])

        print(tabulate(table, headers=['Name', 'Container', 'Status', 'Ip', 'Port']))
    
    @ex(
        help='List the benchmark\'s programs',
        arguments=[
            (['-n', '--name'], {'help': 'The name of the benchmark', 'type': str, 'required': False})
        ]
    )
    def programs(self):
        orbis_handler = self.app.handler.get('handlers', 'orbis', setup=True)
        container_manager = self.app.handler.get('managers', 'container', setup=True)

        if self.app.pargs.name:
            benchmarks = container_manager.find('benchmark', self.app.pargs.name)
        else:
            benchmarks = container_manager.find_all('benchmark')

        if not benchmarks:
            self.app.log.warning(
                f"No  benchmarks found {self.app.pargs.name}. Make sure the benchmark's configs is registered.")

        for benchmark in benchmarks:
            container_manager.start(benchmark.id)
            programs = orbis_handler.get_programs(benchmark)
            print(tabulate([[program] for program in programs], headers=['Name']))

    @ex(
        help='Setups the benchmark\'s container.',
        arguments=[
            (['-F', '--force'],
             {'help': 'Forces the setup of the containers.', 'action': 'store_true', 'required': False}),
            (["-N", "--name"], {'help': "The name of the target benchmark", 'type': str, 'required': True})
        ]
    )
    def setup(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        orbis_handler = self.app.handler.get('handlers', 'orbis', setup=True)
        container_manager.setup(self.app.pargs.name, kind=self.Meta.label, api_handler=orbis_handler,
                                force=self.app.pargs.force)

    @ex(
        help='Creates the Nexus',
        arguments=[
            (["-N", "--name"], {'help': "The name of the target tool", 'type': str, 'required': True})
        ]
    )
    def create(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        container_manager.create(self.app.pargs.name, kind=self.Meta.label)

    @ex(
        help='Launches orbis server on setup benchmark container',
        arguments=[
            (["-N", "--name"], {'help': "The name of the target tool", 'type': str, 'required': True})
        ]
    )
    def serve(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        orbis_handler = self.app.handler.get('handlers', 'orbis', setup=True)
        container_manager.serve(self.app.pargs.name, kind=self.Meta.label, api_handler=orbis_handler)

    @ex(
        help='Refreshes the IP of the benchmark\'s container in the database.',
        arguments=[
            (["-N", "--name"], {'help': "The name of the target benchmark", 'type': str, 'required': True})
        ]
    )
    def refresh(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        container_manager.refresh(self.app.pargs.name, kind=self.Meta.label)

    @ex(
        help='Deletes the benchmarks records',
        arguments=[
            (['-rm', '--remove'], {'help': 'Removes the associated containers', 'action': 'store_true', 'required': False})
        ]
    )
    def delete(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        container_manager.delete(self.Meta.label, remove=self.app.pargs.remove)
