from agent import ask_agent
from tools.file_reader import list_files
from config import PROJECT_PATH, NVIDIA_MODEL


def main():
    print("SuperCoder Local v1")
    print("===================")
    print(f"Project path: {PROJECT_PATH}")
    print(f"Model: {NVIDIA_MODEL}")
    print()

    files = list_files()

    print("Files found:")
    if files:
        for file in files:
            print(f"- {file}")
    else:
        print("No files found.")

    print()
    task = input("What do you want the agent to do?\n ")

    print()
    print("Thinking...")
    print()

    answer = ask_agent(task)

    print("AGENT ANSWER")
    print("============")
    print(answer)


if __name__ == "__main__":
    main()
