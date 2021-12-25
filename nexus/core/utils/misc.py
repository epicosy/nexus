import tarfile
import io

from git import Repo, RemoteProgress
from binascii import b2a_hex
from os import urandom
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm


class CloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm()

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()


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


def get_repo(path: str, repo_path: str, logger) -> Repo:
    project_path = Path(path, repo_path.split('/')[-1])

    if project_path.exists():
        logger.info(f"Repo {repo_path} found locally.")
        repo = Repo(project_path)

        if repo.bare:
            logger.warning(f"Bare repo {repo_path}")
    else:
        logger.info(f"Cloning {repo_path} to {project_path}")
        repo = Repo.clone_from(url=f"https://github.com/{repo_path}", to_path=project_path, progress=CloneProgress())
        logger.info(f"Cloned {repo_path}")
    
    return repo
