import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import file_reader


class ListFilesTests(unittest.TestCase):
    def test_ignores_junk_directories_and_sorts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "b.py").write_text("x")
            (project / "a.py").write_text("x")

            for directory, filename in [
                (".venv", "ignored.py"),
                ("node_modules", "ignored.js"),
                (".git", "ignored.py"),
            ]:
                path = project / directory
                path.mkdir()
                (path / filename).write_text("x")

            with patch.object(file_reader, "PROJECT_PATH", project):
                files = file_reader.list_files()

        self.assertEqual(files, ["a.py", "b.py"])


if __name__ == "__main__":
    unittest.main()
