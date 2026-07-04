import json

from tools.file_reader import list_files, read_file
from tools.code_search import search_code


def run_tool(action: str, args: dict) -> str:
    """
    Executes the tool requested by the agent.

    The model does not directly access your computer.
    It only asks for an action.
    Python decides if the action is allowed.
    """

    try:
        if action == "list_files":
            files = list_files()
            return json.dumps(
                {
                    "success": True,
                    "files": files,
                },
                indent=2,
            )

        if action == "read_file":
            path = args.get("path")

            if not path:
                return json.dumps(
                    {
                        "success": False,
                        "error": "Missing argument: path",
                    },
                    indent=2,
                )

            content = read_file(path)
            return json.dumps(
                {
                    "success": True,
                    "path": path,
                    "content": content,
                },
                indent=2,
            )

        if action == "search_code":
            query = args.get("query")

            if not query:
                return json.dumps(
                    {
                        "success": False,
                        "error": "Missing argument: query",
                    },
                    indent=2,
                )

            results = search_code(query)
            return json.dumps(
                {
                    "success": True,
                    "query": query,
                    "matching_files": results,
                },
                indent=2,
            )

        return json.dumps(
            {
                "success": False,
                "error": f"Unknown action: {action}",
            },
            indent=2,
        )

    except Exception as error:
        return json.dumps(
            {
                "success": False,
                "error": str(error),
            },
            indent=2,
        ) 
    