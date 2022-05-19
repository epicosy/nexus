import binascii
import os
import re
from pathlib import Path

from nexus.core.data.context import Context
from nexus.core.data.program import Manifest
from nexus.core.data.store import Program, Signal, Command, Vulnerability
from nexus.core.handlers.nexus import NexusHandler


def c_to_cpp(c_file: str):
    if '.cc' in c_file:
        return re.sub(r'.cc$', '.ii', c_file)
    return re.sub(r'.c$', '.i', c_file)


class ProphetCGC(NexusHandler):
    class Meta:
        label = 'prophet_cgc'

    def __init__(self, **kw):
        super().__init__(tool='prophet32', benchmark='cgc', **kw)

    def run(self, program: Program, vulnerability: Vulnerability, context: Context):
        manifest = vulnerability.get_manifest()
        working_dir = Path(f"{program.name}_{binascii.b2a_hex(os.urandom(4)).decode()}")
        working_dir_src = working_dir / 'src'
        working_dir_profile = working_dir / 'profile'
        program_instance_src = self.orbis.checkout(context.benchmark.instance, vuln=vulnerability,
                                                   working_dir=working_dir_src)
        program_instance_profile = self.orbis.checkout(context.benchmark.instance, vuln=vulnerability,
                                                       working_dir=working_dir_profile)

        self.orbis.build(context.benchmark.instance, program_instance=program_instance_src,
                         args={'env': {'CC': 'gcc', 'CXX': 'gcc'}, 'set': {'m64': True}})

        self.orbis.build(context.benchmark.instance, program_instance=program_instance_profile,
                         args={'env': {'CC': 'gcc', 'CXX': 'gcc'}, 'set': {'m64': True}})

        test_command = Command(iid=program_instance_profile.iid,
                               url=self.orbis.url(action='test', instance=context.benchmark.instance),
                               vid=vulnerability.id)
        test_command.add_arg('exit_fail')
        test_command.add_arg('neg_pov')
        test_command.add_placeholder(name='tests', value='cases')
        test_signal = Signal(arg='test_cmd', command=test_command)

        build_command = Command(iid=program_instance_profile.iid,
                                url=self.orbis.url(action='build', instance=context.benchmark.instance),
                                vid=vulnerability.id)
        build_command.add_arg('exit_err')
        build_command.add_arg('link')
        build_command.add_arg('set', {'m64': True})
        build_command.add_placeholder(name='working_dir', value='out_dir')

        build_command.add_param('build_args', {k: v + ' -fPIE' for k, v in program_instance_profile.build_args.items()})
        build_command.add_param('link_cmd', program_instance_profile.link_cmd)
        build_command.add_param('build_dir', str(program_instance_profile.build_dir.parent.parent))
        #        build_command.add_placeholder(name='write_build_args', value='dryrun_src')
        compile_signal = Signal(arg='build_cmd', command=build_command)

        args = {
            'pos_tests': len(program.oracle['cases']),
            'neg_tests': len(vulnerability.oracle['cases'])
        }

        response = self.synapser.repair(signals=[test_signal, compile_signal], args=args,
                                        program_instance=program_instance_profile, manifest=manifest.locs,
                                        instance=context.tool.instance, iid=program_instance_profile.iid)
        response_json = response.json()
        self.app.log.info("CID: " + str(response_json['rid']))
        '''
        if response.ok:
            test_command = Command(iid=program_instance_src.iid,
                                   url=self.orbis.url(action='test', instance=context.benchmark.instance),
                                   vid=vulnerability.id)
            test_command.add_arg('exit_fail')
            test_command.add_arg('neg_pov')
            test_command.add_placeholder(name='tests', value='cases')
            test_signal = Signal(arg='test_cmd', command=test_command)

            build_command = Command(iid=program_instance_src.iid,
                                    url=self.orbis.url(action='build', instance=context.benchmark.instance),
                                    vid=vulnerability.id)
            build_command.add_arg('exit_err')
            build_command.add_arg('set', {'m64': True})
            build_command.add_placeholder(name='working_dir', value='out_dir')
            build_command.add_param('build_args', program_instance_src.build_args)
            build_command.add_param('link_cmd', program_instance_src.link_cmd)

            #        build_command.add_param('build_dir', str(program_instance.build_dir.parent.parent))
            #        build_command.add_placeholder(name='write_build_args', value='dryrun_src')
            compile_signal = Signal(arg='build_cmd', command=build_command)

            args = {
                'pos_tests': len(program.oracle['cases']),
                'neg_tests': len(vulnerability.oracle['cases'])
            }
            response = self.synapser.repair(signals=[test_signal, compile_signal], args=args,
                                            program_instance=program_instance_src, manifest=manifest.locs,
                                            instance=context.tool.instance, iid=program_instance_src.iid)
            response_json = response.json()
            self.app.log.info("RID: " + str(response_json['rid']))
    '''


def load(app):
    app.handler.register(ProphetCGC)
