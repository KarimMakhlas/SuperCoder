import json

from tools.file_reader import list_files, read_file
from tools.code_search import search_code
from tools.command_runner import run_command
from tools.project_summary import summarize_project
from tools.file_writer import write_file_with_approval
from tools.file_editor import edit_file_with_approval


def _error(message: str) -> str:
    return json.dumps({"success": False, "error": message}, indent=2)


def _require(args: dict, *names: str, allow_empty: tuple[str, ...] = ()) -> str | None:
    """
    Returns an error JSON string for the first missing arg, or None if all are present.

    Names in allow_empty only reject None (an empty string is a valid value,
    e.g. old_text/new_text/content). Other names also reject an empty string.
    """

    for name in names:
        value = args.get(name)
        missing = value is None if name in allow_empty else not value

        if missing:
            return _error(f"Missing argument: {name}")

    return None


def run_tool(action: str, args: dict) -> str:
    """
    Executes the tool requested by the agent.

    The model does not directly access your computer.
    It only asks for an action.
    Python decides if the action is allowed.
    """

    try:
        if action == "list_files":
            return json.dumps({"success": True, "files": list_files()}, indent=2)

        if action == "summarize_project":
            return json.dumps({"success": True, "summary": summarize_project()}, indent=2)

        if action == "read_file":
            if error := _require(args, "path"):
                return error

            path = args["path"]
            content = read_file(path)

            return json.dumps({"success": True, "path": path, "content": content}, indent=2)

        if action == "search_code":
            if error := _require(args, "query"):
                return error

            query = args["query"]
            results = search_code(query)

            return json.dumps({"success": True, "query": query, "matches": results}, indent=2)

        if action == "run_command":
            if error := _require(args, "command"):
                return error

            result = run_command(args["command"])

            return json.dumps(result, indent=2)

        if action == "edit_file":
            if error := _require(args, "path", "old_text", "new_text", allow_empty=("old_text", "new_text")):
                return error

            result = edit_file_with_approval(args["path"], args["old_text"], args["new_text"])

            return json.dumps(result, indent=2)

        if action == "write_file":
            if error := _require(args, "path", "content", allow_empty=("content",)):
                return error

            result = write_file_with_approval(args["path"], args["content"])

            return json.dumps(result, indent=2)

        return _error(f"Unknown action: {action}")

    except Exception as error:
        return _error(str(error))
