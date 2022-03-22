from pathlib import Path

from nexus.core.data.context import Context
from nexus.core.data.program import Manifest
from nexus.core.data.store import Program, Signal, Command, Vulnerability
from nexus.core.handlers.nexus import NexusHandler


class JGenProgVul4jRepairTask(NexusHandler):
    class Meta:
        label = 'jgenprog_vul4j'

    def __init__(self, **kw):
        super().__init__(tool='jgenprog', benchmark='vul4j', **kw)

    def run(self, program: Program, vulnerability: Vulnerability, context: Context):
        program_instance = self.orbis.checkout(context.benchmark.instance, vuln=vulnerability)
        self.orbis.build(context.benchmark.instance, program_instance=program_instance, args={})

        args = {
            'src': '',
            'test': '',
            'src_class': '',
            'test_class': '',
            'classpath': '',
        }

        manifest = Manifest([Path("empty")], {})

        response = self.synapser.repair(signals=[], args=args,
                                        program_instance=program_instance, manifest=manifest.locs,
                                        instance=context.tool.instance)
        response_json = response.json()
        self.app.log.info("RID: " + str(response_json['rid']))


def load(app):
    app.handler.register(JGenProgVul4jRepairTask)
