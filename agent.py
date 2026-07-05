import json
from json import JSONDecodeError

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config import NVIDIA_MODEL
from tools.tool_runner import run_tool
from run_logger import create_run_log, add_step, finish_run_log, save_run_log


MAX_STEPS = 8


def load_system_prompt() -> str:
    with open("prompts/system_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def create_model() -> ChatNVIDIA:
    return ChatNVIDIA(
        model=NVIDIA_MODEL,
        temperature=0.2,
        max_completion_tokens=1600,
    )


def parse_agent_response(response_text: str) -> dict:
    """
    The model should return JSON.

    But sometimes it may return extra text before or after the JSON.
    This function tries to extract the JSON object safely.
    """

    response_text = response_text.strip()

    try:
        return json.loads(response_text)
    except JSONDecodeError:
        pass

    start_index = response_text.find("{")
    end_index = response_text.rfind("}")

    if start_index == -1 or end_index == -1 or end_index <= start_index:
        raise ValueError(
            "The model did not return a JSON object.\n\n"
            f"Model response was:\n{response_text}"
        )

    possible_json = response_text[start_index : end_index + 1]

    try:
        return json.loads(possible_json)
    except JSONDecodeError as error:
        raise ValueError(
            "The model returned invalid JSON.\n\n"
            f"Extracted JSON was:\n{possible_json}\n\n"
            f"Original response was:\n{response_text}\n\n"
            f"JSON error:\n{error}"
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
        "read_file",
        "search_code",
        "run_command",
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

    The model can return either:
    1. {"answer": "..."}
    2. Structured fields like file, function, problem, etc.
    """

    if "answer" in args:
        return args["answer"]

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


def build_initial_prompt(task: str) -> str:
    system_prompt = load_system_prompt()

    return f"""
{system_prompt}

USER TASK:
{task}

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
    prompt = build_initial_prompt(task)

    used_actions = set()
    run_log = create_run_log(task)

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

        if action == "final_answer":
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

        action_key = action_to_key(action, args)

        if action_key in used_actions:
            tool_result = json.dumps(
                {
                    "success": False,
                    "error": (
                        "You already used this exact action before. "
                        "Do not repeat the same tool call. Choose a different action "
                        "or provide a final_answer if you have enough information."
                    ),
                },
                indent=2,
            )
        else:
            used_actions.add(action_key)
            tool_result = run_tool(action, args)

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
