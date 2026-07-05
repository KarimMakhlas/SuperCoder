import json
from json import JSONDecodeError
from pathlib import Path

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config import NVIDIA_MODEL
from tools.tool_runner import run_tool
from run_logger import create_run_log, add_step, finish_run_log, save_run_log


MAX_STEPS = 8

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "system_prompt.txt"

MODIFYING_ACTIONS = {"edit_file", "write_file"}


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def create_model() -> ChatNVIDIA:
    return ChatNVIDIA(
        model=NVIDIA_MODEL,
        temperature=0.2,
        max_completion_tokens=1600,
    )


def classify_task(task: str) -> str:
    """
    Classifies the user task into a simple task type.

    Important:
    Modification intent must be checked before bug analysis.
    Example:
    "Fix the division by zero bug" should be code_modification,
    not only bug_analysis.
    """

    task_lower = task.lower()

    modification_keywords = [
        "fix",
        "update",
        "modify",
        "change",
        "implement",
        "add",
        "remove",
        "refactor",
        "rewrite",
        "improve the code",
        "make it",
    ]

    bug_keywords = [
        "bug",
        "error",
        "issue",
        "crash",
        "fail",
        "failing",
        "exception",
        "traceback",
        "broken",
    ]

    review_keywords = [
        "review",
        "quality",
        "clean",
        "best practice",
        "maintainability",
    ]

    explanation_keywords = [
        "explain",
        "understand",
        "what does",
        "how does",
        "describe",
    ]

    summary_keywords = [
        "summary",
        "summarize",
        "structure",
        "architecture",
        "overview",
    ]

    if any(keyword in task_lower for keyword in modification_keywords):
        return "code_modification"

    if any(keyword in task_lower for keyword in bug_keywords):
        return "bug_analysis"

    if any(keyword in task_lower for keyword in review_keywords):
        return "code_review"

    if any(keyword in task_lower for keyword in explanation_keywords):
        return "code_explanation"

    if any(keyword in task_lower for keyword in summary_keywords):
        return "project_summary"

    return "general"


def parse_agent_response(response_text: str) -> dict:
    """
    Extracts the first valid JSON object returned by the model.

    Why this is needed:
    Sometimes the model returns extra explanations, markdown code fences,
    or multiple JSON examples. We only want the first valid action object.
    """

    response_text = response_text.strip()

    # First try: maybe the whole response is already valid JSON.
    try:
        parsed = json.loads(response_text)

        if isinstance(parsed, dict) and "action" in parsed:
            return parsed
    except JSONDecodeError:
        pass

    decoder = json.JSONDecoder()

    # Try to decode JSON starting from every "{" in the response.
    for index, char in enumerate(response_text):
        if char != "{":
            continue

        try:
            parsed, _ = decoder.raw_decode(response_text[index:])

            if isinstance(parsed, dict) and "action" in parsed:
                return parsed

        except JSONDecodeError:
            continue

    raise ValueError(
        "The model did not return a valid JSON action object.\n\n"
        f"Model response was:\n{response_text}"
    )


def validate_agent_action(parsed_response: dict) -> dict:
    """
    Validates that the model returned the expected structure.

    Expected:
    {
        "action": "list_files",
        "args": {}
    }
    """

    allowed_actions = {
        "list_files",
        "summarize_project",
        "read_file",
        "search_code",
        "run_command",
        "edit_file",
        "write_file",
        "final_answer",
    }

    action = parsed_response.get("action")
    args = parsed_response.get("args")

    if action not in allowed_actions:
        raise ValueError(f"Invalid action from model: {action}")

    if args is None:
        parsed_response["args"] = {}

    if not isinstance(parsed_response["args"], dict):
        raise ValueError("Invalid args from model: args must be a dictionary.")

    return parsed_response


def action_to_key(action: str, args: dict) -> str:
    """
    Converts an action + args into a stable string.

    Example:
    action = "read_file"
    args = {"path": "calculator.py"}

    Result:
    read_file:{"path": "calculator.py"}
    """

    return f"{action}:{json.dumps(args, sort_keys=True)}"


def format_final_answer(args: dict) -> str:
    """
    Formats the final answer returned by the model.

    Supported formats:
    1. General answer
    2. Bug analysis
    3. Code review
    4. Implementation summary
    """

    if "answer" in args:
        return args["answer"]

    # Implementation summary format
    if any(key in args for key in ["changed_files", "changes_made", "verification", "status"]):
        sections = []

        status = args.get("status")
        changed_files = args.get("changed_files", [])
        changes_made = args.get("changes_made", [])
        verification = args.get("verification")
        next_steps = args.get("next_steps", [])

        if status:
            sections.append(f"Status:\n{status}")

        if changed_files:
            sections.append("Changed files:")
            for file in changed_files:
                sections.append(f"- {file}")

        if changes_made:
            sections.append("Changes made:")
            for change in changes_made:
                sections.append(f"- {change}")

        if verification:
            sections.append(f"Verification:\n{verification}")

        if next_steps:
            sections.append("Next steps:")
            for step in next_steps:
                sections.append(f"- {step}")

        return "\n".join(sections)

    # Code review format
    if any(key in args for key in ["summary", "strengths", "issues", "recommendations", "next_steps"]):
        sections = []

        summary = args.get("summary")
        strengths = args.get("strengths", [])
        issues = args.get("issues", [])
        recommendations = args.get("recommendations", [])
        next_steps = args.get("next_steps", [])

        if summary:
            sections.append(f"Summary:\n{summary}")

        if strengths:
            sections.append("Strengths:")
            for strength in strengths:
                sections.append(f"- {strength}")

        if issues:
            sections.append("Issues:")
            for issue in issues:
                if isinstance(issue, dict):
                    file = issue.get("file", "Unknown file")
                    severity = issue.get("severity", "medium")
                    description = issue.get("description", "")
                    recommendation = issue.get("recommendation", "")

                    sections.append(f"- [{severity}] {file}: {description}")

                    if recommendation:
                        sections.append(f"  Recommendation: {recommendation}")
                else:
                    sections.append(f"- {issue}")

        if recommendations:
            sections.append("Recommendations:")
            for recommendation in recommendations:
                sections.append(f"- {recommendation}")

        if next_steps:
            sections.append("Next steps:")
            for step in next_steps:
                sections.append(f"- {step}")

        return "\n".join(sections)

    # Bug analysis format
    sections = []

    fields = [
        ("File", args.get("file")),
        ("Function", args.get("function")),
        ("Problem", args.get("problem")),
        ("Why it fails", args.get("why_it_fails")),
        ("Impact", args.get("impact")),
        ("Evidence", args.get("evidence")),
        ("Command run", args.get("command_run")),
        ("Suggested fix", args.get("suggested_fix")),
    ]

    for label, value in fields:
        if value:
            sections.append(f"{label}: {value}")

    if not sections:
        return "The agent returned a final answer, but it did not include useful details."

    return "\n".join(sections)


def build_initial_prompt(task: str, task_type: str) -> str:
    system_prompt = load_system_prompt()

    return f"""
{system_prompt}

USER TASK:
{task}

TASK TYPE:
{task_type}

Use the task type to choose the best strategy and final answer format.

Start by choosing the best action.
Remember: respond with exactly one JSON object.
"""


def build_next_prompt(
    previous_prompt: str,
    agent_response: str,
    tool_result: str,
) -> str:
    return f"""
{previous_prompt}

AGENT ACTION:
{agent_response}

TOOL RESULT:
{tool_result}

Now choose the next best action.
Remember: respond with exactly one JSON object.
"""


def ask_agent(task: str) -> str:
    model = create_model()
    task_type = classify_task(task)
    prompt = build_initial_prompt(task, task_type)

    print(f"[classifier] Task type: {task_type}")
    print()

    used_actions = set()
    run_log = create_run_log(task)
    run_log["task_type"] = task_type

    modification_attempted = False

    try:
        for step in range(1, MAX_STEPS + 1):
            print(f"[agent step {step}] Asking model...")

            response = model.invoke(prompt)
            response_text = response.content.strip()

            print(f"[agent step {step}] Model response:")
            print(response_text)
            print()

            parsed_response = parse_agent_response(response_text)
            parsed_response = validate_agent_action(parsed_response)

            action = parsed_response.get("action")
            args = parsed_response.get("args", {})

            final_answer_blocked = (
                action == "final_answer"
                and task_type == "code_modification"
                and not modification_attempted
            )

            if action == "final_answer" and not final_answer_blocked:
                final_answer = format_final_answer(args)

                add_step(
                    run_log=run_log,
                    step_number=step,
                    model_response=response_text,
                    action=action,
                    args=args,
                    tool_result=None,
                )

                finish_run_log(run_log, final_answer)
                log_path = save_run_log(run_log)

                print(f"[log] Run saved to: {log_path}")

                return final_answer

            if final_answer_blocked:
                tool_result = json.dumps(
                    {
                        "success": False,
                        "error": (
                            "This is a code_modification task. You must call "
                            "edit_file or write_file (and have it either succeed "
                            "or be explicitly rejected by the user) before giving "
                            "a final_answer."
                        ),
                    },
                    indent=2,
                )
            else:
                repeat_protected_actions = {
                    "list_files",
                    "summarize_project",
                    "read_file",
                    "search_code",
                }

                action_key = action_to_key(action, args)

                if action in repeat_protected_actions and action_key in used_actions:
                    tool_result = json.dumps(
                        {
                            "success": False,
                            "error": (
                                "You already used this exact read-only action before. "
                                "Do not repeat the same tool call. Choose a different action "
                                "or provide a final_answer if you have enough information."
                            ),
                        },
                        indent=2,
                    )
                else:
                    if action in repeat_protected_actions:
                        used_actions.add(action_key)

                    tool_result = run_tool(action, args)

            if action in MODIFYING_ACTIONS:
                try:
                    result_data = json.loads(tool_result)
                except JSONDecodeError:
                    result_data = {}

                if result_data.get("success") or result_data.get("approved") is False:
                    modification_attempted = True

            add_step(
                run_log=run_log,
                step_number=step,
                model_response=response_text,
                action=action,
                args=args,
                tool_result=tool_result,
            )

            print(f"[agent step {step}] Tool result:")
            print(tool_result)
            print()

            prompt = build_next_prompt(
                previous_prompt=prompt,
                agent_response=response_text,
                tool_result=tool_result,
            )

        final_answer = (
            "The agent reached the maximum number of steps without a final answer. "
            "Try asking a smaller or more precise task."
        )

        finish_run_log(run_log, final_answer)
        log_path = save_run_log(run_log)

        print(f"[log] Run saved to: {log_path}")

        return final_answer

    except Exception as error:
        finish_run_log(run_log, f"Agent run failed with an error: {error}")
        log_path = save_run_log(run_log)

        print(f"[log] Run saved to: {log_path}")

        raise
