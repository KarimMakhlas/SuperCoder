from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config import NVIDIA_MODEL
from tools.file_reader import list_files, read_file


def load_system_prompt() -> str:
    with open("prompts/system_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def build_project_context() -> str:
    files = list_files()

    context_parts = []

    context_parts.append("PROJECT FILES:")
    if files:
        context_parts.append("\n".join(files))
    else:
        context_parts.append("No readable files found.")

    context_parts.append("\n\nFILE CONTENTS:")

    for file in files:
        content = read_file(file)
        context_parts.append(f"\n--- {file} ---\n{content}")

    return "\n".join(context_parts)


def ask_agent(task: str) -> str:
    system_prompt = load_system_prompt()
    project_context = build_project_context()

    prompt = f"""
{system_prompt}

USER TASK:
{task}

PROJECT CONTEXT:
{project_context}
"""

    model = ChatNVIDIA(
        model=NVIDIA_MODEL,
        temperature=0.2,
        max_completion_tokens=1200,
    )

    response = model.invoke(prompt)

    return response.content
