from collections import Counter
from pathlib import Path

from config import PROJECT_PATH
from tools.file_reader import list_files


def detect_project_type(files: list[str]) -> list[str]:
    """
    Detects the project type using file names and extensions.
    """

    detected = []

    file_set = set(files)
    extensions = {Path(file).suffix for file in files}

    if "package.json" in file_set:
        detected.append("Node.js / JavaScript / TypeScript")

    if "pom.xml" in file_set or "build.gradle" in file_set or "build.gradle.kts" in file_set:
        detected.append("Java / JVM")

    if "requirements.txt" in file_set or "pyproject.toml" in file_set or ".py" in extensions:
        detected.append("Python")

    if any(file.endswith(".csproj") for file in files) or any(file.endswith(".sln") for file in files):
        detected.append(".NET / C#")

    if "go.mod" in file_set:
        detected.append("Go")

    if "Cargo.toml" in file_set:
        detected.append("Rust")

    if "composer.json" in file_set:
        detected.append("PHP")

    if not detected:
        detected.append("Unknown / generic code project")

    return detected


def find_important_files(files: list[str]) -> list[str]:
    """
    Finds files that are usually important in a project.
    """

    important_names = {
        "README.md",
        "readme.md",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "docker-compose.yml",
        "Dockerfile",
        "main.py",
        "app.py",
        "server.py",
        "index.js",
        "index.ts",
        "main.ts",
    }

    important_files = []

    for file in files:
        name = Path(file).name

        if name in important_names:
            important_files.append(file)

    return important_files


def find_possible_entry_points(files: list[str]) -> list[str]:
    """
    Finds files that may be used to start the application.
    """

    entry_points = []

    entry_names = {
        "main.py",
        "app.py",
        "server.py",
        "calculator.py",
        "index.js",
        "index.ts",
        "main.ts",
        "main.java",
        "Program.cs",
    }

    for file in files:
        name = Path(file).name

        if name in entry_names:
            entry_points.append(file)

    return entry_points


def summarize_project() -> dict:
    """
    Builds a simple summary of the project.
    """

    files = list_files()
    extensions = Counter(Path(file).suffix or "[no extension]" for file in files)

    return {
        "project_path": str(PROJECT_PATH),
        "total_files": len(files),
        "detected_project_type": detect_project_type(files),
        "extensions": dict(extensions),
        "important_files": find_important_files(files),
        "possible_entry_points": find_possible_entry_points(files),
        "files": files,
    }
