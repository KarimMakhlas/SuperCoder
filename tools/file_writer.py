from config import PROJECT_PATH
from tools.path_utils import apply_change_with_approval, validate_existing_allowed_file


def validate_write_path(relative_path: str):
    """
    Validates that the file is inside the project folder, exists,
    and has an allowed extension.

    For v2.0, the agent can only modify existing files.
    """

    try:
        return validate_existing_allowed_file(relative_path, PROJECT_PATH)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"File not found: {relative_path}. "
            "For v2.0, the agent can only modify existing files."
        )


def write_file_with_approval(relative_path: str, new_content: str) -> dict:
    """
    Shows a diff and asks the user for approval before writing.
    """

    file_path = validate_write_path(relative_path)
    old_content = file_path.read_text(encoding="utf-8", errors="ignore")[:100_000]

    return apply_change_with_approval(
        file_path=file_path,
        relative_path=relative_path,
        old_content=old_content,
        new_content=new_content,
        header="PROPOSED FILE CHANGE",
        unchanged_message="No changes needed. The new content is identical to the current file.",
        rejected_message="User rejected the proposed file change.",
        applied_message="File updated successfully after user approval.",
    )
