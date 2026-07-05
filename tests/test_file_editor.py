import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import file_editor, file_reader


class EditFileTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name)
        self.target = self.project / "sample.py"
        self.path_patches = [
            patch.object(file_editor, "PROJECT_PATH", self.project),
            patch.object(file_reader, "PROJECT_PATH", self.project),
        ]
        for path_patch in self.path_patches:
            path_patch.start()

    def tearDown(self):
        for path_patch in self.path_patches:
            path_patch.stop()
        self.temp_dir.cleanup()

    def test_applies_approved_edit(self):
        self.target.write_text("print('hello')\n")

        with patch("builtins.input", return_value="YES"):
            result = file_editor.edit_file_with_approval(
                "sample.py", "print('hello')", "print('goodbye')"
            )

        self.assertTrue(result["success"])
        self.assertTrue(result["approved"])
        self.assertEqual(self.target.read_text(), "print('goodbye')\n")

    def test_rejects_ambiguous_old_text(self):
        self.target.write_text("x = 1\nx = 1\n")

        result = file_editor.edit_file_with_approval(
            "sample.py", "x = 1", "x = 2"
        )

        self.assertFalse(result["success"])
        self.assertIn("ambiguous", result["error"])

    def test_does_not_apply_rejected_edit(self):
        self.target.write_text("print('hello')\n")

        with patch("builtins.input", return_value="no"):
            result = file_editor.edit_file_with_approval(
                "sample.py", "print('hello')", "print('goodbye')"
            )

        self.assertFalse(result["success"])
        self.assertFalse(result["approved"])
        self.assertEqual(self.target.read_text(), "print('hello')\n")


if __name__ == "__main__":
    unittest.main()
