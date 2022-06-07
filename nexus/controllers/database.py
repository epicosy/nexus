from cement import Controller, ex
from docker.errors import APIError
from tabulate import tabulate

from nexus.core.database import Instance


class Database(Controller):
    class Meta:
        label = 'database'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help='Deletes tables from database.',
        arguments=[
            (['-C', '--containers'], {'help': 'Flag to remove associated containers.', 'action': 'store_true',
                                      'required': False}),
            (['-V', '--volumes'], {'help': 'Flag to remove associated volumes.', 'action': 'store_true',
                                   'required': False})
        ]
    )
    def destroy(self):
        self.app.log.warning(f"This operation will delete all tables in the database: {self.app.db.engine.url}")
        res = input("Are you sure you want to continue this operation? (y/n) ")

        if res in ["Yes", "Y", "y", "yes"]:
            container_manager = self.app.handler.get('managers', 'container', setup=True)

            if self.app.pargs.containers:
                for instance in container_manager.all():
                    try:
                        container_manager.remove(instance)
                    except APIError as ae:
                        self.app.log.error(str(ae))

            self.app.db.destroy()

    @ex(
        help='Lists specified table in the database.',
        arguments=[
            (['-N', '--nexus'], {'help': 'Lists all nexuses in the database.', 'action': 'store_true', 'required': False}),
            (['-C', '--containers'], {'help': 'Lists containers in the database.', 'action': 'store_true',
                                      'required': False})
        ]
    )
    def list(self):
        '''
        if self.app.pargs.nexus:
            nexuses = self.app.db.query(NexusData)
            table = [[nexus.id, nexus.name, nexus.tid[:10], nexus.bid[:10], nexus.status] for nexus in nexuses]
            print(tabulate(table, headers=['Id', 'Name', 'Tool Id', 'Benchmark Id', 'Status']))
        '''

        if self.app.pargs.containers:
            container_handler = self.app.handler.get('managers', 'container', setup=True)
            containers = container_handler.all()
            table = [[c.id[:10], c.name, c.image[:10], c.volume, c.status, c.kind, c.ip, c.port] for c in containers]
            print(tabulate(table, headers=['Id', 'Name', 'Image Id', 'Volume', 'Status', 'Type', 'IP', 'Port']))

    @ex(
        help='Deletes container records',
        arguments=[
            (['-N', '--name'], {'help': 'Name of the container', 'type': str, 'required': True}),
            (['-K', '--kind'], {'help': 'Tool/benchmark', 'choices': ['tool', 'benchmark']})
        ]
    )
    def delete(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        instance = container_manager.find(self.app.pargs.kind, name=self.app.pargs.name)

        self.app.log.warning(f"Deleting {instance}")
        res = input("Are you sure you want to continue this operation? (y/n) ")

        if res in ["Yes", "Y", "y", "yes"]:
            self.app.db.delete(Instance, instance.id)
