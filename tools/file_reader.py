from pathlib import Path
from config import PROJECT_PATH

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".kt",
    ".cs",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".html",
    ".css",
}


def is_allowed_file(path: Path) -> bool:
    return path.suffix in ALLOWED_EXTENSIONS


def list_files() -> list[str]:
    files = []

    for path in PROJECT_PATH.rglob("*"):
        if path.is_file() and is_allowed_file(path):
            relative_path = path.relative_to(PROJECT_PATH)
            files.append(str(relative_path))

    return files


def read_file(relative_path: str, max_chars: int = 6000) -> str:
    file_path = (PROJECT_PATH / relative_path).resolve()

    # Security: prevent reading outside the project folder
    if not str(file_path).startswith(str(PROJECT_PATH)):
        raise ValueError("Security error: trying to read outside the project folder.")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")

    if not is_allowed_file(file_path):
        raise ValueError(f"File type not allowed: {file_path.suffix}")

    content = file_path.read_text(encoding="utf-8", errors="ignore")

    return content[:max_chars]