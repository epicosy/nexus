from dataclasses import dataclass
from pathlib import Path
from typing import List, AnyStr


@dataclass
class Manifest:
    files: List[Path]

    def __len__(self):
        return len(self.files)

    def write(self, path: Path) -> Path:
        manifest_file = path / 'manifest.txt'

        with manifest_file.open(mode="w") as op:
            for file in self.files:
                op.write(f"{file}\n")

        return manifest_file

    def extensions(self) -> List[AnyStr]:
        return [file.suffix for file in self.files]
