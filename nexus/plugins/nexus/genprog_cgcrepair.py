import re

from nexus.core.data.context import Context
from nexus.core.data.store import Task
from nexus.core.exc import CommandError, NexusError
from nexus.core.handlers.nexus import NexusHandler


def c_to_cpp(c_file: str):
    if '.cc' in c_file:
        return re.sub(r'.cc$', '.ii', c_file)
    return re.sub(r'.c$', '.i', c_file)


class GenprogCGCRepairTask(NexusHandler):
    class Meta:
        label = 'genprog_cgcrepair'

    def __init__(self, **kw):
        super().__init__(tool='genprog', benchmark='cgcrepair', **kw)

    def run(self, task: Task, context: Context):
        try:
            task.program.manifest.transform(c_to_cpp)
            iid, working_dir = context.orbis.checkout(context.benchmark,
                                                      args={'pid': task.program.id,
                                                            'root_dir': f"/{context.benchmark.volume}"})
            _, build_path = context.orbis.compile(context.benchmark, args={'iid': iid, 'args': {'--save_temps': ''}})
            #task.program.manifest.add_parent(build_path)
            container_manager = self.app.handler.get('managers', 'container', setup=True)
            tool_container = container_manager.get(context.tool.id)
            manifest_file = context.synapser.write(container=tool_container, name="manifest.txt", path=working_dir,
                                                   data=task.program.manifest.format(delimiter='\n'))

            signals = {
                '--test-command': {
                    'url': context.orbis.url(endpoint='test', instance=context.benchmark),
                    'data': {
                        'iid': iid,
                        'args': {
                             '--exit_fail': '',
                             '--neg_pov': ''
                        }
                    },
                    'placeholders': {
                        '--tests': '__TEST_NAME__'
                    }
                },
                '--compiler-command': {
                    'url': context.orbis.url(endpoint='compile', instance=context.benchmark),
                    'data': {
                        'iid': iid,
                        'args': {
                             '--cpp_files': '',
                             '--exit_err': '',
                             '--inst_files': task.program.manifest.format(delimiter=' '),
                        }
                    },
                    'placeholders': {
                        '--fix_files': '__SOURCE_NAME__'
                    }
                }
            }

            args = {
                '--program': str(manifest_file),
                '--prefix': str(build_path),
                '--rep': "cilpatch" if len(task.program.manifest) > 1 else "c",
                '--pos-tests': len(task.program.tests.pos),
                '--neg-tests': len(task.program.tests.neg)
            }

            response = context.synapser.repair(signals=signals, args=args, working_dir=working_dir,
                                               instance=context.tool).json()

            task.patches = context.synapser.get_patches(context.tool)
            task.fix = context.synapser.get_patches(context.tool, fixes=True)
        except (CommandError, NexusError) as err:
            task.error(str(err))
            self.app.log.error(str(err))


def load(app):
    app.handler.register(GenprogCGCRepairTask)
