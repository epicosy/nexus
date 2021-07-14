from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import List, AnyStr

from nexus.core.data.program import Tests
from nexus.core.data.results import CommandData


@dataclass
class Store:
    assets = {}

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
class Vulnerability:
    id: str
    cwe: str
    program: str
    exploit: str
    cve: str = '-'


@dataclass
class Program(Store):
    working_dir: Path
    name: str
    vuln: Vulnerability
    root: Path
    source: Path = None
    lib: Path = None
    include: Path = None

    def has_source(self):
        return self.source and self.source.exists()

    def has_lib(self):
        return self.lib and self.lib.exists()

    def has_include(self):
        return self.include and self.include.exists()


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
class Task(Store):
    vuln: str
    status: str = None
    start_date: datetime = None
    end_date: datetime = None
    fix: Patch = None
    patches: List[Patch] = field(default_factory=lambda: [])
    tests: Tests = None
    err: AnyStr = None
    cmds: List[CommandData] = field(default_factory=lambda: [])

    def add_command(self, cmd: CommandData):
        self.cmds.append(cmd)

    def duration(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).total_seconds()
        return 0

    def has_patches(self):
        return self.patches not in (None, [])

    def has_fix(self):
        return self.fix not in (None, [])

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

        if self.has_fix():
            self.status = "Repaired"
        elif self.has_patches():
            self.status = "Patched"
        elif errors:
            self.error('\n'.join(errors))
        elif [c for c in self.cmds if c.timeout]:
            self.status = "Timeout"
        elif self.has_started():
            self.status = "Done"
        else:
            self.status = "Finished"

        self.end_date = datetime.now()

    def __str__(self):
        fix = f"\tFix:\n{self.fix}\n" if self.fix else ""
        patches = f"\tGenerated {len(self.patches)} patches\n" if self.patches else ""
        stats = f"Status:\n\t\t{self.status}\n\t\tStart: {self.start_date}\n\t\tEnd: {self.end_date}\n"

        return f"{self.vuln} repair task:\n\t{stats}" + patches + fix


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
