from pathlib import Path
from typing import List, Dict


def write_bash(cmd: str, name: str, path: Path, mode: oct = 0o777) -> Path:
    bash_file = path / (name + ".sh")

    with bash_file.open(mode="w") as bf:
        bf.write(f"#!/bin/bash\n{cmd}")
    bash_file.chmod(mode)

    return bash_file


def args_to_str(args: dict) -> str:
    arg_str = ""
    for opt, arg in args.items():
        arg_str += f" {opt} {arg}" if arg else f" {opt}"

    return arg_str


def match_patches(sources: List[Path], program_root_dir: Path, patch_root_dir: Path) -> Dict[Path, Path]:
    patch_files = [f.relative_to(patch_root_dir) for f in patch_root_dir.glob("**/*.*")]
    return {(program_root_dir / file): (patch_root_dir / file) for file in sources if file in patch_files}
