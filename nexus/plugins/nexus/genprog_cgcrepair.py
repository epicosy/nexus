import re

from nexus.core.data.context import Context
from nexus.core.data.program import Manifest
from nexus.core.data.store import Program, Signal, Command, Vulnerability
from nexus.core.handlers.nexus import NexusHandler


def c_to_cpp(c_file: str):
    if '.cc' in c_file:
        return re.sub(r'.cc$', '.ii', c_file)
    return re.sub(r'.c$', '.i', c_file)


class GenprogCGCRepairTask(NexusHandler):
    class Meta:
        label = 'genprog_cgcrepair'

    def __init__(self, **kw):
        super().__init__(tool='genprog', benchmark='cgc', **kw)

    def run(self, program: Program, vulnerability: Vulnerability, context: Context):
        manifest = vulnerability.get_manifest()
        manifest.transform(c_to_cpp)
        program_instance = self.orbis.checkout(context.benchmark.instance, vuln=vulnerability)
        self.orbis.build(context.benchmark.instance, program_instance=program_instance, args={'save_temps': True})

        test_command = Command(iid=program_instance.iid,
                               url=self.orbis.url(action='test', instance=context.benchmark.instance))
        test_command.add_arg('exit_fail')
        test_command.add_arg('neg_pov')
        test_command.add_arg('replace_neg_fmt', ['n', 'pov_'])
        test_command.add_arg('replace_pos_fmt', ['p', 't'])
        test_command.add_placeholder(name='tests', value='__TEST_NAME__')
        test_signal = Signal(arg='--test-command', command=test_command)

        build_command = Command(iid=program_instance.iid,
                                  url=self.orbis.url(action='build', instance=context.benchmark.instance))
        build_command.add_arg('cpp_files')
        build_command.add_arg('exit_err')
        build_command.add_arg('save_temps')
        build_command.add_arg('replace_ext', ['.c', '.i'])
        build_command.add_arg(name='inst_files', value=manifest.format(delimiter=' '))
        build_command.add_placeholder(name='fix_files', value='__SOURCE_NAME__')
        compile_signal = Signal(arg='--compiler-command', command=build_command)

        args = {
            '--pos-tests': len(program.oracle['cases']),
            '--neg-tests': len(vulnerability.oracle['cases'])
        }
        response = self.synapser.repair(signals=[test_signal, compile_signal], args=args,
                                        program_instance=program_instance, manifest=manifest.locs,
                                        instance=context.tool.instance)
        response_json = response.json()
        self.app.log.info("RID: " + str(response_json['rid']))


def load(app):
    app.handler.register(GenprogCGCRepairTask)
