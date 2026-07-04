import json
from json import JSONDecodeError

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config import NVIDIA_MODEL
from tools.tool_runner import run_tool


MAX_STEPS = 8


def load_system_prompt() -> str:
    with open("prompts/system_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def create_model() -> ChatNVIDIA:
    return ChatNVIDIA(
        model=NVIDIA_MODEL,
        temperature=0.2,
        max_completion_tokens=1200,
    )


def parse_agent_response(response_text: str) -> dict:
    """
    The model should return JSON.

    Example:
    {"action": "list_files", "args": {}}

    Sometimes models add extra text by mistake.
    For now, we keep it simple and expect valid JSON.
    """

    try:
        return json.loads(response_text)
    except JSONDecodeError as error:
        raise ValueError(
            f"The model did not return valid JSON.\n\n"
            f"Model response was:\n{response_text}\n\n"
            f"JSON error:\n{error}"
        )


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

    for step in range(1, MAX_STEPS + 1):
        print(f"[agent step {step}] Asking model...")

        response = model.invoke(prompt)
        response_text = response.content.strip()

        print(f"[agent step {step}] Model response:")
        print(response_text)
        print()

        parsed_response = parse_agent_response(response_text)

        action = parsed_response.get("action")
        args = parsed_response.get("args", {})

        if action == "final_answer":
            return args.get("answer", "The agent returned an empty final answer.")

        tool_result = run_tool(action, args)

        print(f"[agent step {step}] Tool result:")
        print(tool_result)
        print()

        prompt = build_next_prompt(
            previous_prompt=prompt,
            agent_response=response_text,
            tool_result=tool_result,
        )

    return (
        "The agent reached the maximum number of steps without a final answer. "
        "Try asking a smaller or more precise task."
    )