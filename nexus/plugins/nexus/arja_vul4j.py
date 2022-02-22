from pathlib import Path

from nexus.core.data.context import Context
from nexus.core.data.program import Manifest
from nexus.core.data.store import Program, Signal, Command, Vulnerability
from nexus.core.handlers.nexus import NexusHandler


class ArjaVul4jRepairTask(NexusHandler):
    class Meta:
        label = 'arja_vul4j'

    def __init__(self, **kw):
        super().__init__(tool='arja', benchmark='vul4j', **kw)

    def run(self, program: Program, vulnerability: Vulnerability, context: Context):
        program_instance = self.orbis.checkout(context.benchmark.instance, program=program)
        self.orbis.compile(context.benchmark.instance, program_instance=program_instance, args={})

        args = {
            'src': '',
            'src_class': '',
            'test_class': '',
            'classpath': '',
            'perfect_fl_dir': '',
            'test_cmd': ''
        }

        manifest = Manifest([Path("empty")])

        response = self.synapser.repair(signals=[], args=args,
                                        program_instance=program_instance, manifest=manifest,
                                        instance=context.tool.instance)
        response_json = response.json()
        self.app.log.info("RID: " + str(response_json['rid']))


def load(app):
    app.handler.register(ArjaVul4jRepairTask)
