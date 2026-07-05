import json
from datetime import datetime
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent / "logs" / "runs"


def create_run_log(task: str) -> dict:
    """
    Creates the initial run log object.
    """

    return {
        "task": task,
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "steps": [],
        "final_answer": None,
    }


def add_step(
    run_log: dict,
    step_number: int,
    model_response: str,
    action: str,
    args: dict,
    tool_result: str | None = None,
) -> None:
    """
    Adds one step to the run log.
    """

    run_log["steps"].append(
        {
            "step": step_number,
            "model_response": model_response,
            "action": action,
            "args": args,
            "tool_result": tool_result,
        }
    )


def finish_run_log(run_log: dict, final_answer: str) -> None:
    """
    Marks the run as finished.
    """

    run_log["finished_at"] = datetime.now().isoformat()
    run_log["final_answer"] = final_answer


def save_run_log(run_log: dict) -> str:
    """
    Saves the run log to logs/runs/.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    file_path = LOG_DIR / f"run_{timestamp}.json"

    file_path.write_text(
        json.dumps(run_log, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return str(file_path)