import re

from nexus.core.data.context import Context
from nexus.core.data.store import Program, Signal, Command, Vulnerability
from nexus.core.handlers.nexus import NexusHandler


def c_to_cpp(c_file: str):
    if '.cc' in c_file:
        return re.sub(r'.cc$', '.ii', c_file)
    return re.sub(r'.c$', '.i', c_file)


class MUTAPRCGCRepairTask(NexusHandler):
    class Meta:
        label = 'mutapr_cgcrepair'

    def __init__(self, **kw):
        super().__init__(tool='mutapr', benchmark='cgcrepair', **kw)

    def run(self, program: Program, vulnerability: Vulnerability, context: Context):
        manifest = program.get_manifest()
        manifest.transform(c_to_cpp)

        program_instance = self.orbis.checkout(context.benchmark.instance, program=program)
        self.orbis.compile(context.benchmark.instance, program_instance=program_instance, args={'--save_temps': ''})

        # COVERAGE COMPILE
        compile_command = Command(iid=program_instance.iid, args={'--cpp_files': '', '--exit_err': ''},
                                  url=self.orbis.url(action='compile', instance=context.benchmark.instance),
                                  placeholders={'--inst_files': '__INST_FILES__'})

        # COVERAGE POS TESTS
        pos_test_command = Command(iid=program_instance.iid, args={'--pos_tests': ''},
                                   url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                   placeholders={"--cov_out_dir": "__COV_OUT_DIR__",
                                                 "--rename_suffix": "__RENAME_SUFFIX__"})

        # COVERAGE NEG TESTS
        neg_test_command = Command(iid=program_instance.iid, args={'--neg_tests': ''},
                                   url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                   placeholders={"--cov_out_dir": "__COV_OUT_DIR__"})

        response = self.synapser.coverage(signals=[Signal(arg='compile', command=compile_command),
                                                   Signal(arg='pos_tests', command=pos_test_command),
                                                   Signal(arg='neg_tests', command=neg_test_command)],
                                          program_instance=program_instance, manifest=manifest,
                                          instance=context.tool.instance)
        response_json = response.json()
        self.app.log.info("CID: " + str(response_json['cid']))

        if response.ok:
            # REPAIR COMPILE
            pos_test_command = Command(iid=program_instance.iid, args={'--exit_fail': '', '--pos_tests': ''},
                                       url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                       placeholders={"--out_file": "__EXTRA__"})

            neg_test_command = Command(iid=program_instance.iid,
                                       url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                       args={'--exit_fail': '', '--neg_tests': '', '--neg_pov': ''},
                                       placeholders={"--out_file": "__EXTRA__"})

            compile_command = Command(iid=program_instance.iid,
                                      url=self.orbis.url(action='compile', instance=context.benchmark.instance),
                                      args={'--inst_files': manifest.format(delimiter=' '), '--cpp_files': '',
                                            '--exit_err': ''},
                                      placeholders={"--fix_files": "__EXTRA__"})

            # REPAIR
            response = self.synapser.repair(signals=[Signal(arg='--gcc', command=compile_command),
                                                     Signal(arg='--good', command=pos_test_command),
                                                     Signal(arg='--bad', command=neg_test_command)],
                                            args={'--vn': 0},
                                            program_instance=program_instance, manifest=manifest,
                                            instance=context.tool.instance)
            response_json = response.json()
            self.app.log.info("RID: " + str(response_json['rid']))


def load(app):
    app.handler.register(MUTAPRCGCRepairTask)
