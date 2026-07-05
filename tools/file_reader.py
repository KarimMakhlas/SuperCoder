import os
from pathlib import Path

from config import PROJECT_PATH
from tools.path_utils import is_allowed_file, validate_existing_allowed_file


IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "logs",
}


def list_files() -> list[str]:
    files = []

    for root, dir_names, file_names in os.walk(PROJECT_PATH):
        dir_names[:] = [name for name in dir_names if name not in IGNORED_DIR_NAMES]

        for file_name in file_names:
            path = Path(root) / file_name

            if is_allowed_file(path):
                files.append(str(path.relative_to(PROJECT_PATH)))

    return sorted(files)


def read_file(relative_path: str, max_chars: int = 6000) -> str:
    file_path = validate_existing_allowed_file(relative_path, PROJECT_PATH)

    content = file_path.read_text(encoding="utf-8", errors="ignore")

    return content[:max_chars]
