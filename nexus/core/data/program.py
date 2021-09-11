from dataclasses import dataclass
from pathlib import Path
from typing import List, AnyStr, Callable


@dataclass
class Manifest:
    files: List[Path]

    def __len__(self):
        return len(self.files)

    def transform(self, func: Callable):
        """
            func: callable with str input and str output
        """
        self.files = [Path(func(str(file))) for file in self.files]

    def add_parent(self, path: Path):
        self.files = [path / file for file in self.files]

    def format(self, delimiter: str = '\n') -> str:
        return delimiter.join([str(file) for file in self.files])

    def extensions(self) -> List[AnyStr]:
        return [file.suffix for file in self.files]
