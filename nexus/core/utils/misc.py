import tarfile
import io

from binascii import b2a_hex
from os import urandom
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


def str_to_tarfile(data: str, tar_info_name: str) -> Path:
    random = b2a_hex(urandom(2)).decode()
    dest_path = Path('/tmp', random + ".tar")

    info = tarfile.TarInfo(name=tar_info_name)
    info.size = len(data)

    with tarfile.TarFile(str(dest_path), 'w') as tar:
        tar.addfile(info, io.BytesIO(data.encode('utf8')))

    return dest_path
