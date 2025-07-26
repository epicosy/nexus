import re

from nexus.core.data.context import Context
from nexus.core.data.store import Task
from nexus.core.exc import CommandError, NexusError
from nexus.core.handlers.nexus import NexusHandler


def c_to_cpp(c_file: str):
    if '.cc' in c_file:
        return re.sub(r'.cc$', '.ii', c_file)
    return re.sub(r'.c$', '.i', c_file)


class ExtractFixCGCRepairTask(NexusHandler):
    class Meta:
        label = 'extractfix_cgcrepair'

    def __init__(self, **kw):
        super().__init__(tool='extractfix', benchmark='cgcrepair', **kw)

    def run(self, task: Task, context: Context):
        try:
            task.program.manifest.transform(c_to_cpp)
            iid, working_dir = self.orbis.checkout(context.benchmark,
                                                      args={'pid': task.program.id,
                                                            'root_dir': f"/{context.benchmark.volume}"})
            container_manager = self.app.handler.get('managers', 'container', setup=True)
            tool_container = container_manager.get(context.tool.id)
            context.tool.mkdir(path=working_dir, container=tool_container)
            context.tool.mkdir(path=working_dir / 'project', container=tool_container)

            signals = {
                '--tests': {
                    'url': self.orbis.url(endpoint='test', instance=context.benchmark),
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
                '--run-command': {
                    'url': self.orbis.url(endpoint='compile', instance=context.benchmark),
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
            # TODO: get bug_type from program's vulnerability
            args = {
                '--source-path': working_dir / 'project',
                '--bug-type': task.program.vuln.cwe,
                '--binary-name': task.program.manifest.files[0].stem
            }

            response = self.synapser.repair(signals=signals, args=args, working_dir=working_dir,
                                            target=task.program.manifest.files[0],
                                            instance=context.tool)
            response_json = response.json()

            self.app.log.info("RID: " + str(response_json['rid']))

        except (CommandError, NexusError) as err:
            task.error(str(err))
            self.app.log.error(str(err))

    def config_script(self, program, nexus):
        # TODO: implement this
        pass

    def build_script(self, program, nexus):
        # TODO: implement this
        pass

    def compile_script(self, program, nexus):
        # TODO: implement this
        pass

    def test_script(self, program, nexus):
        # TODO: implement this
        pass

    def get_bug_type(self, program) -> str:
        # TODO: implement this
        pass


def load(app):
    app.handler.register(ExtractFixCGCRepairTask)
