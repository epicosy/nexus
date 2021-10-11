from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import List, AnyStr

from nexus.core.data.program import Manifest
from nexus.core.data.results import CommandData


@dataclass
class Store:
    assets: dict = field(default_factory=lambda: {})

    def __getitem__(self, key: str):
        return self.assets[key]

    def __setitem__(self, key: str, value):
        self.assets[key] = value

    def __iter__(self):
        return iter(self.assets)

    def keys(self):
        return self.assets.keys()

    def items(self):
        return self.assets.items()

    def values(self):
        return self.assets.values()


@dataclass
class Command:
    iid: int
    action: str
    args = Store()
    placeholders = Store()

    def add_arg(self, name: str, value: str = ''):
        self.args[name] = value

    def add_placeholder(self, name: str, value: str):
        self.placeholders[name] = value

    def to_dict(self):
        return {'data': {'iid': self.iid, 'args': self.args}, 'placeholders': self.placeholders}


@dataclass
class Signal:
    arg: str
    command: Command


@dataclass
class Vulnerability:
    id: str
    pid: str
    cwe: str
    program: str
    povs: List[str]
    related: List[str] = None
    cve: str = '-'


@dataclass
class Program:
    id: str
    vulns: List[str]
    tests: List[str]
    name: str
    manifest: List[str]
    root: Path = None
    source: Path = None
    lib: Path = None
    include: Path = None

    def has_source(self):
        return self.source and self.source.exists()

    def has_lib(self):
        return self.lib and self.lib.exists()

    def has_include(self):
        return self.include and self.include.exists()

    def get_manifest(self) -> Manifest:
        return Manifest([Path(file) for file in self.manifest])


@dataclass
class Diff:
    source_file: Path
    patch_file: Path
    change: AnyStr

    def __str__(self):
        return f"{self.source_file.name} {self.patch_file.name}\n{self.change}"


@dataclass
class Patch:
    is_fix: bool
    diffs: List[Diff] = field(default_factory=lambda: [])

    def add(self, diff: Diff):
        self.diffs.append(diff)

    def __str__(self):
        return '\n'.join([str(d) for d in self.diffs])


@dataclass
class ProgramInstance:
    iid: int
    working_dir: Path
    build_dir: Path = None

    def to_dict(self):
        return {'iid': self.iid, 'working_dir': self.working_dir, 'build_dir': self.build_dir}


@dataclass
class Task:
    program: Program
    status: str = None
    start_date: datetime = None
    end_date: datetime = None
    err: AnyStr = None
    cmds: List[CommandData] = field(default_factory=lambda: [])

    def add_command(self, cmd: CommandData):
        self.cmds.append(cmd)

    def duration(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).total_seconds()
        return 0

    def has_started(self):
        return self.status == "Started"

    def start(self):
        self.start_date = datetime.now()
        self.status = "Started"

    def wait(self):
        self.status = "Waiting"

    def error(self, msg: AnyStr):
        self.status = "Error"
        self.err = msg
        self.end_date = datetime.now()

    def done(self):
        errors = [c.args + "\n" + str(c.error) for c in self.cmds if c and c.error]

        if errors:
            self.error('\n'.join(errors))
        elif [c for c in self.cmds if c.timeout]:
            self.status = "Timeout"
        elif self.has_started():
            self.status = "Done"
        else:
            self.status = "Finished"

        self.end_date = datetime.now()

    def __str__(self):
        stats = f"Status:\n\t\t{self.status}\n\t\tStart: {self.start_date}\n\t\tEnd: {self.end_date}\n"

        return f"{self.program.id} repair task:\n\t{stats}"


@dataclass
class Runner(Store):
    tasks: List[Task] = field(default_factory=lambda: [])
    finished: List[Task] = field(default_factory=lambda: [])
    running: List[Task] = field(default_factory=lambda: [])
    waiting: List[Task] = field(default_factory=lambda: [])

    def done(self, task: Task):
        task.done()
        self.finished += [task]
        self.running.remove(task)
