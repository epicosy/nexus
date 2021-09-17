import asyncio
import websockets

from tabulate import tabulate
from cement import Controller, ex


class Tool(Controller):
    class Meta:
        label = 'tool'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help='Lists registered tools'
    )
    def list(self):
        tool_manager = self.app.handler.get('manager', self.Meta.label, setup=True)
        table = []

        for tool, _ in tool_manager.all():
            container = tool.container.short_id if tool.container else None
            status = tool.container.status if container else '-'
            table.append([tool.name, tool.enabled, tool.loaded, container if container else '-', status])

        print(tabulate(table, headers=['Tool', 'Enabled', 'Loaded', 'Container', 'Status']))

    @ex(
        help='Setups the tool\'s container.',
        arguments=[
            (['-F', '--force'],
             {'help': 'Forces the setup of the containers.', 'action': 'store_true', 'required': False}),
            (["-N", "--name"], {'help': "The name of the target tool", 'type': str, 'required': True})
        ]
    )
    def setup(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        synapser_handler = self.app.handler.get('handlers', 'synapser', setup=True)
        container_manager.setup(self.app.pargs.name, kind=self.Meta.label, force=self.app.pargs.force,
                                api_handler=synapser_handler)

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
        help='Deletes the benchmarks records',
        arguments=[
            (['-rm', '--remove'],
             {'help': 'Removes the associated containers', 'action': 'store_true', 'required': False})
        ]
    )
    def delete(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        container_manager.delete(self.Meta.label, remove=self.app.pargs.remove)

    @ex(
        help='Stream repair instance\'s execution output',
        arguments=[
            (['--id'], {'help': 'The repair instance id.', 'type': int, 'required': True}),
            (['--name'], {'help': 'The name of the repair tool.', 'type': str, 'required': True})
        ]
    )
    def stream(self):
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        tool = container_manager.find('tool', self.app.pargs.name)

        synapser = self.app.handler.get('handlers', 'synapser', setup=True)
        response = synapser.stream(tool, rid=self.app.pargs.id)
        response_json = response.json()

        if 'socket' in response_json:
            ws_url = f"ws://{tool.ip}:{response_json['socket']}"

            async def read():
                async with websockets.connect(ws_url) as websocket:
                    try:
                        while True:
                            msg = await websocket.recv()
                            self.app.log.info(msg, ws_url)
                    except KeyboardInterrupt:
                        pass

            asyncio.run(read())
