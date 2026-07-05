from config import PROJECT_PATH
from tools.path_utils import apply_change_with_approval, validate_existing_allowed_file


def validate_edit_path(relative_path: str):
    return validate_existing_allowed_file(relative_path, PROJECT_PATH)


def edit_file_with_approval(relative_path: str, old_text: str, new_text: str) -> dict:
    """
    Safely edits part of a file.

    The edit only works if old_text is found exactly once.
    This prevents accidental large rewrites.
    """

    file_path = validate_edit_path(relative_path)
    old_content = file_path.read_text(encoding="utf-8", errors="ignore")[:100_000]

    if not old_text:
        return {
            "success": False,
            "error": "old_text cannot be empty.",
        }

    occurrences = old_content.count(old_text)

    if occurrences == 0:
        return {
            "success": False,
            "error": "old_text was not found in the file. The edit cannot be applied safely.",
        }

    if occurrences > 1:
        return {
            "success": False,
            "error": (
                f"old_text was found {occurrences} times. "
                "The edit is ambiguous and cannot be applied safely."
            ),
        }

    new_content = old_content.replace(old_text, new_text, 1)

    return apply_change_with_approval(
        file_path=file_path,
        relative_path=relative_path,
        old_content=old_content,
        new_content=new_content,
        header="PROPOSED PARTIAL FILE EDIT",
        unchanged_message="No changes needed.",
        rejected_message="User rejected the proposed edit.",
        applied_message="Partial edit applied successfully after user approval.",
    )
