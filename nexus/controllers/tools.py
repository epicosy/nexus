from tabulate import tabulate
from cement import Controller, ex


class Tools(Controller):
    class Meta:
        label = 'tools'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help='Lists registered tools'
    )
    def list(self):
        tool_manager = self.app.handler.get('manager', 'tool', setup=True)
        table = []

        for tool in tool_manager.get():
            table.append([tool.name, tool.enabled, tool.loaded, tool.container.id if tool.container else '-'])

        print(tabulate(table, headers=['Tool', 'Enabled', 'Loaded', 'Container']))
