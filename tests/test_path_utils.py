import tempfile
import unittest
from pathlib import Path

from tools.path_utils import resolve_within_project


class ResolveWithinProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_allows_nested_path(self):
        expected = self.project / "sub" / "file.py"
        expected.parent.mkdir()
        expected.write_text("x")

        resolved = resolve_within_project("sub/file.py", self.project)

        self.assertEqual(resolved, expected.resolve())

    def test_rejects_parent_traversal(self):
        with self.assertRaises(ValueError):
            resolve_within_project("../../etc/passwd", self.project)

    def test_rejects_sibling_prefix_attack(self):
        project = self.project / "proj"
        project.mkdir()
        evil = self.project / "proj_evil"
        evil.mkdir()
        (evil / "secret.py").write_text("x")

        with self.assertRaises(ValueError):
            resolve_within_project("../proj_evil/secret.py", project)


if __name__ == "__main__":
    unittest.main()
