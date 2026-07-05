import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import command_runner
from tools.command_runner import run_command


class RunCommandTests(unittest.TestCase):
    def run_in_temporary_project(self, command):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(command_runner, "PROJECT_PATH", Path(temp_dir)):
                return run_command(command)

    def test_success_when_return_code_is_zero(self):
        result = self.run_in_temporary_project('python3 -c "pass"')

        self.assertTrue(result["success"])
        self.assertEqual(result["return_code"], 0)

    def test_failure_when_return_code_is_nonzero(self):
        result = self.run_in_temporary_project(
            'python3 -c "import sys; sys.exit(1)"'
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["return_code"], 1)


if __name__ == "__main__":
    unittest.main()
