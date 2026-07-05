import difflib
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


def resolve_within_project(relative_path: str, project_path: Path = PROJECT_PATH) -> Path:
    """
    Resolves relative_path against project_path and guarantees the
    result is actually inside project_path (rejects "../" traversal
    and sibling-directory prefix tricks like /proj vs /proj_evil).
    """

    resolved = (project_path / relative_path).resolve()

    if not resolved.is_relative_to(project_path):
        raise ValueError(
            f"Security error: '{relative_path}' resolves outside the project folder."
        )

    return resolved


def validate_existing_allowed_file(
    relative_path: str,
    project_path: Path = PROJECT_PATH,
) -> Path:
    """
    Resolves relative_path safely, and checks that it exists and has
    an allowed extension.
    """

    file_path = resolve_within_project(relative_path, project_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")

    if not is_allowed_file(file_path):
        raise ValueError(f"File type not allowed: {file_path.suffix}")

    return file_path


def build_unified_diff(relative_path: str, old_content: str, new_content: str) -> str:
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"{relative_path} (before)",
        tofile=f"{relative_path} (after)",
    )

    return "".join(diff)


def apply_change_with_approval(
    file_path: Path,
    relative_path: str,
    old_content: str,
    new_content: str,
    header: str,
    unchanged_message: str,
    rejected_message: str,
    applied_message: str,
) -> dict:
    """
    Shared approval flow for edit_file/write_file: shows a diff, asks the
    user to type YES, and writes the file only if approved.
    """

    if old_content == new_content:
        return {
            "success": True,
            "path": relative_path,
            "changed": False,
            "message": unchanged_message,
        }

    diff = build_unified_diff(relative_path, old_content, new_content)

    print()
    print(header)
    print("=" * len(header))
    print(diff)
    print()

    approval = input("Approve this change? Type YES to apply, anything else to reject:\n> ")

    if approval != "YES":
        return {
            "success": False,
            "approved": False,
            "path": relative_path,
            "changed": False,
            "message": rejected_message,
        }

    file_path.write_text(new_content, encoding="utf-8")

    return {
        "success": True,
        "approved": True,
        "path": relative_path,
        "changed": True,
        "message": applied_message,
    }
