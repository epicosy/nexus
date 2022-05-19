import re

from nexus.core.data.context import Context
from nexus.core.data.store import Program, Signal, Command, Vulnerability
from nexus.core.handlers.nexus import NexusHandler


def c_to_cpp(c_file: str):
    if '.cc' in c_file:
        return re.sub(r'.cc$', '.ii', c_file)
    return re.sub(r'.c$', '.i', c_file)


class MUTAPRCGCTask(NexusHandler):
    class Meta:
        label = 'mutapr_cgc'

    def __init__(self, **kw):
        super().__init__(tool='mutapr', benchmark='cgc', **kw)

    def run(self, program: Program, vulnerability: Vulnerability, context: Context):
        manifest = vulnerability.get_manifest()
        manifest.transform(c_to_cpp)

        program_instance = self.orbis.checkout(context.benchmark.instance, vuln=vulnerability)
        self.orbis.build(context.benchmark.instance, program_instance=program_instance, args={'save_temps': True})
        manifest_path = vulnerability.get_manifest()
        manifest_path.add_parent(program_instance.working_dir)
        inst_files = manifest_path.to_str()

        # COVERAGE COMPILE
        compile_command = Command(iid=program_instance.iid, args={'cpp_files': True, 'exit_err': True,
                                                                  'inst_files': inst_files},
                                  url=self.orbis.url(action='build', instance=context.benchmark.instance),
                                  placeholders={'fix_files': '__INST_FILES__'}, vid=vulnerability.id)

        # COVERAGE POS TESTS
        pos_test_command = Command(iid=program_instance.iid, args={'tests': list(program.oracle['cases'].keys())},
                                   url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                   vid=vulnerability.id, placeholders={"cov_out_dir": "__COV_OUT_DIR__",
                                                                       "rename_suffix": "__RENAME_SUFFIX__"})
        pos_test_command.add_arg('cov_suffix', '.path')
        pos_test_command.add_arg('cov_dir', str(program_instance.build_dir))
        # COVERAGE NEG TESTS
        neg_test_command = Command(iid=program_instance.iid, args={'tests': list(vulnerability.oracle['cases'].keys())},
                                   url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                   vid=vulnerability.id, placeholders={"cov_out_dir": "__COV_OUT_DIR__"})

        neg_test_command.add_arg('cov_suffix', '.path')
        neg_test_command.add_arg('cov_dir', str(program_instance.build_dir))

        response = self.synapser.coverage(signals=[Signal(arg='--gcc', command=compile_command),
                                                   Signal(arg='--good', command=pos_test_command),
                                                   Signal(arg='--bad', command=neg_test_command)],
                                          program_instance=program_instance, manifest=manifest,
                                          instance=context.tool.instance, iid=program_instance.iid)
        response_json = response.json()
        self.app.log.info("CID: " + str(response_json['cid']))

        if response.ok:
            # REPAIR COMPILE
            pos_test_command = Command(iid=program_instance.iid, args={'exit_fail': True, 'timeout': 10,
                                                                       'tests': list(program.oracle['cases'].keys())},
                                       url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                       placeholders={"out_file": "out_file"}, vid=vulnerability.id)

            neg_test_command = Command(iid=program_instance.iid,
                                       url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                       args={'exit_fail': True, 'tests': list(vulnerability.oracle['cases'].keys()),
                                             'neg_pov': True, 'timeout': 10},
                                       placeholders={"out_file": "out_file"}, vid=vulnerability.id)

            compile_command = Command(iid=program_instance.iid,
                                      url=self.orbis.url(action='build', instance=context.benchmark.instance),
                                      args={'inst_files': manifest_path.to_str(), 'cpp_files': True,
                                            'exit_err': True},
                                      placeholders={"fix_files": "out_file"}, vid=vulnerability.id)

            # REPAIR
            response = self.synapser.repair(signals=[Signal(arg='--gcc', command=compile_command),
                                                     Signal(arg='--good', command=pos_test_command),
                                                     Signal(arg='--bad', command=neg_test_command)],
                                            args={'--vn': 0},
                                            program_instance=program_instance, manifest=manifest.locs,
                                            instance=context.tool.instance, iid=program_instance.iid)
            response_json = response.json()
            self.app.log.info("RID: " + str(response_json['rid']))


def load(app):
    app.handler.register(MUTAPRCGCTask)
