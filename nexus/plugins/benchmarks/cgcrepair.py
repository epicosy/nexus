import re
from pathlib import Path
from typing import Union, List, Dict

from nexus.core.data.program import Manifest
from nexus.core.data.results import CommandData
from nexus.core.data.store import Program, Vulnerability
from nexus.core.exc import NexusError
from nexus.core.handlers.benchmark import BenchmarkHandler
from nexus.core.handlers.nexus import LocalNexus
from nexus.core.handlers.nexus import RemoteNexus


class CGCRepairLocal(LocalNexus):
    """
        Interface to local CGCRepair benchmark
    """
    class Meta:
        label = 'cgcrepair_local_nexus'

    def get_programs(self, **kwargs) -> CommandData:
        return super().__call__(cmd_str=f"cgcrepair database list --metadata --name", raise_err=True, **kwargs)

    def get_vulns(self, **kwargs) -> Dict[str, Vulnerability]:
        vulns_data = super().__call__(cmd_str=f"cgcrepair database cwes", raise_err=True, **kwargs)
        vulns = {}

        for line in vulns_data.output.strip().split('\n'):
            if line.startswith('CWE'):
                cwe, _id, program, exploit = line.split(' ')
                vulns[_id] = Vulnerability(id=_id, cwe=cwe, program=program, exploit=exploit)

        return vulns

    def get_tests(self, program: Program, **kwargs) -> List[str]:
        tests_cmd = self(cmd_str=f"cgcrepair -vb corpus --cid {program.vuln.id} tests --count", raise_err=True, **kwargs)

        return [f"p{n}" for n in range(1, int(tests_cmd.output)+1)]

    def get_manifest(self, program: Program, **kwargs) -> Manifest:
        manifest_cmd = self(cmd_str=f"cgcrepair -vb corpus -cn {program.name} manifest", raise_err=True, **kwargs)
        files = manifest_cmd.output.splitlines()

        return Manifest([Path(file) for file in files if file != ''])

    def checkout(self, program: Program, **kwargs) -> CommandData:
        return super().__call__(cmd_str=f"cgcrepair -vb corpus -cn {program.name} checkout -wd {program.working_dir} -rp",
                                **kwargs)

    def make(self, program: Program, **kwargs) -> CommandData:
        return super().__call__(cmd_str=f"cgcrepair -vb instance --id {program['id']} make", **kwargs)

    def compile(self, program: Program, **kwargs) -> CommandData:
        if 'args' in kwargs:
            kwargs['args'] += " 2>&1"
        return super().__call__(cmd_str=f"cgcrepair -vb instance --id {program['id']} compile", **kwargs)

    def test(self, program: Program, **kwargs) -> CommandData:
        if 'args' in kwargs:
            kwargs['args'] += " 2>&1"
        return super().__call__(cmd_str=f"cgcrepair -vb instance --id {program['id']} test", **kwargs)

    def patch(self, program: Program, source: Path, patch: Path, **kwargs) -> CommandData:
        cmd_str = f"cgcrepair -vb instance --id {program['id']} patch --source {source} --file {patch}"
        return super().__call__(cmd_str=cmd_str, **kwargs)


class CGCRepair(BenchmarkHandler):
    """
        Handler for interacting locally with the CGCRepair benchmark
    """
    class Meta:
        label = 'cgcrepair'

    def __init__(self, **kwargs):
        super().__init__(local_nexus='cgcrepair_local_nexus', remote_nexus='cgcrepair_remote_nexus', **kwargs)

    @staticmethod
    def match_id(out: str) -> Union[str, None]:
        match = re.search('id (\d{1,4})', out)
        if match:
            return match.group(1)

        return None

    def get(self, vuln: str, **kwargs) -> Program:
        if vuln not in self.vulns:
            raise NexusError(f"{vuln} not found")

        working_dir = self.get_working_dir(vuln, randomize=True)
        root_dir = working_dir / vuln

        return Program(name=self.vulns[vuln].program, working_dir=working_dir, root=root_dir, source=root_dir / 'src',
                       lib=root_dir / 'lib', include=root_dir / 'include', vuln=self.vulns[vuln])

    def load(self):
        if not self.vulns:
            self.vulns = self.get_nexus().get_vulns(container=self.plugin.container)

    def prepare(self, program: Program, **kwargs):
        nexus = self.get_nexus()
        checkout_cmd = nexus.checkout(program, **kwargs)
        program['id'] = self.match_id(checkout_cmd.output)

        if program['id'] is None:
            id_file = program.working_dir / '.instance_id'

            if id_file.exists():
                program['id'] = id_file.open(mode='r').readlines()[0]
            else:
                raise NexusError("Could not match ID")

        self.app.log.info(f"Prepared {program.name} instance with ID: {program['id']}")

    def prefix(self, program: Program, **kwargs) -> Path:
        return Path(program.working_dir, 'build', program.name, 'CMakeFiles', f"{program.name}.dir")


"""
    def instrumented_files(self, program: Program):
        program['manifest_files']
        inst_files = [nexus['prefix'] / file.name for file in nexus.program.manifest.files]
"""


def load(nexus):
    nexus.handler.register(CGCRepairLocal)
    nexus.handler.register(CGCRepair)
