import json
import unittest
from unittest.mock import patch

import agent


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeModel:
    def __init__(self, responses):
        self._responses = list(responses)

    def invoke(self, _prompt):
        return _FakeResponse(self._responses.pop(0))


class AgentTests(unittest.TestCase):
    def test_parses_plain_json(self):
        parsed = agent.parse_agent_response(
            '{"action": "list_files", "args": {}}'
        )
        self.assertEqual(parsed, {"action": "list_files", "args": {}})

    def test_parses_json_surrounded_by_prose(self):
        parsed = agent.parse_agent_response(
            'Before\n{"action": "read_file", "args": {"path": "a.py"}}\nAfter'
        )
        self.assertEqual(
            parsed,
            {"action": "read_file", "args": {"path": "a.py"}},
        )

    def test_uses_first_valid_action(self):
        parsed = agent.parse_agent_response(
            '{"action": "list_files", "args": {}} '
            '{"action": "read_file", "args": {"path": "a.py"}}'
        )
        self.assertEqual(parsed["action"], "list_files")

    def test_classifies_tasks(self):
        cases = {
            "Fix the division by zero bug": "code_modification",
            "There is a crash when dividing by zero": "bug_analysis",
            "Please review code quality": "code_review",
        }
        for task, expected in cases.items():
            with self.subTest(task=task):
                self.assertEqual(agent.classify_task(task), expected)

    def test_requires_edit_before_finishing_modification(self):
        model = _FakeModel([
            '{"action": "final_answer", "args": {"answer": "too early"}}',
            '{"action": "edit_file", "args": {"path": "a.py", "old_text": "x", "new_text": "y"}}',
            '{"action": "final_answer", "args": {"answer": "done"}}',
        ])

        def successful_edit(action, _args):
            self.assertEqual(action, "edit_file")
            return json.dumps(
                {"success": True, "approved": True, "changed": True}
            )

        with (
            patch.object(agent, "create_model", return_value=model),
            patch.object(agent, "classify_task", return_value="code_modification"),
            patch.object(agent, "run_tool", side_effect=successful_edit),
            patch.object(agent, "save_run_log", return_value="test-log.json"),
        ):
            answer = agent.ask_agent("Fix the bug")

        self.assertEqual(answer, "done")


if __name__ == "__main__":
    unittest.main()
