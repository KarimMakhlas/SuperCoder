import shlex
import subprocess

from config import PROJECT_PATH


ALLOWED_COMMANDS = {
    "python",
    "python3",
    "pytest",
}


DANGEROUS_TOKENS = {
    "rm",
    "sudo",
    "del",
    "format",
    "shutdown",
    "reboot",
    "curl",
    "wget",
    "git",
    "pip",
    "npm",
    "yarn",
    "pnpm",
    "docker",
    "kubectl",
    "chmod",
    "chown",
    ">",
    ">>",
    "|",
    "&&",
    ";",
}


def run_command(command: str, timeout: int = 10) -> dict:
    """
    Runs a safe command inside the project folder.

    We only allow simple commands like:
    - python calculator.py
    - python3 calculator.py
    - pytest
    """

    parts = shlex.split(command)

    if not parts:
        return {
            "success": False,
            "error": "Command is empty.",
        }

    executable = parts[0]

    if executable not in ALLOWED_COMMANDS:
        return {
            "success": False,
            "error": f"Command not allowed: {executable}",
        }

    for token in parts:
        if token in DANGEROUS_TOKENS:
            return {
                "success": False,
                "error": f"Dangerous token not allowed: {token}",
            }

    try:
        result = subprocess.run(
            parts,
            cwd=PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        return {
            "success": result.returncode == 0,
            "command": command,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "command": command,
            "error": f"Command timed out after {timeout} seconds.",
        }

    except Exception as error:
        return {
            "success": False,
            "command": command,
            "error": str(error),
        }
