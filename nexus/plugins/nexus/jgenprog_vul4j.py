from nexus.core.data.context import Context
from nexus.core.data.store import Program, Vulnerability, Command, Signal
from nexus.core.handlers.nexus import NexusHandler


class JGenProgVul4JRepairTask(NexusHandler):
    class Meta:
        label = 'jgenprog_vul4j'

    def __init__(self, **kw):
        super().__init__(tool='jgenprog', benchmark='vul4j', **kw)

    def run(self, program: Program, vulnerability: Vulnerability, context: Context):
        program_modules = program.modules
        vulnerability_manifest = vulnerability.get_manifest()

        # checkout and pre-build the vulnerability
        program_instance = self.orbis.checkout(context.benchmark.instance, vuln=vulnerability)
        self.orbis.build(context.benchmark.instance, program_instance=program_instance, args={})
        cp_res = self.orbis.get_classpath(context.benchmark.instance, program_instance=program_instance)

        # the project named is used to merge with universal working_dir defined here
        # e.g., /nexus/vul4j_a1bc/ ->/nexus/vul4j_a1bc/vul4j
        repair_args = {
            'src': program_modules.get('src_dir'),
            'test': program_modules.get('test_dir'),
            'src_class': program_modules.get('src_classes'),
            'test_class': program_modules.get('test_classes'),
            'jvm_version': program.build.get('version'),
            'classpath': cp_res,
            'project_name': program.name,
            'perfect_data': 'VUL4J/' + vulnerability.id
        }

        # orbis_test_url = self.orbis.url(action='test', instance=context.benchmark.instance)
        orbis_testbatch_url = "http://172.17.0.2:8080/testbatch"  # for only testing on my machine

        test_all_cmd = Command(iid=program_instance.iid,
                               url=orbis_testbatch_url)
        test_all_cmd.add_placeholder(name='batch', value='all')
        test_all_signal = Signal(arg='-testallcmd', command=test_all_cmd)

        test_povs_cmd = Command(iid=program_instance.iid,
                                url=orbis_testbatch_url)
        test_povs_cmd.add_placeholder(name='batch', value='povs')
        test_failing_signal = Signal(arg='-testfailingcmd', command=test_povs_cmd)

        response = self.synapser.repair(signals=[test_all_signal, test_failing_signal], args=repair_args,
                                        program_instance=program_instance,
                                        manifest=vulnerability_manifest.locs,
                                        instance=context.tool.instance)
        response_json = response.json()
        self.app.log.info("RID: " + str(response_json['rid']))


def load(app):
    app.handler.register(JGenProgVul4JRepairTask)
