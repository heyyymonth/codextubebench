import unittest

from tubebench.evaluator import evaluate
from tubebench.state import set_path


class EvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = {
            "success_predicates": [{"path": "tabs.target.playback", "equals": "paused"}],
            "allowed_mutations": ["tabs.target.playback"],
            "forbidden_mutations": ["tabs.other.playback"],
            "optimal_steps": 1,
        }
        self.before = {
            "tabs": {
                "target": {"playback": "playing"},
                "other": {"playback": "playing"},
            }
        }

    def test_disturbance_free_success(self) -> None:
        after = {
            "tabs": {
                "target": {"playback": "paused"},
                "other": {"playback": "playing"},
            }
        }
        result = evaluate(self.task, self.before, after, 1)
        self.assertTrue(result["disturbance_free_success"])

    def test_forbidden_change_blocks_disturbance_free_success(self) -> None:
        after = {
            "tabs": {
                "target": {"playback": "paused"},
                "other": {"playback": "paused"},
            }
        }
        result = evaluate(self.task, self.before, after, 2)
        self.assertTrue(result["exact_success"])
        self.assertFalse(result["disturbance_free_success"])
        self.assertEqual(["tabs.other.playback"], result["side_effects"])

    def test_nested_state_setter(self) -> None:
        state = {}
        set_path(state, "a.b.c", 4)
        self.assertEqual({"a": {"b": {"c": 4}}}, state)

    def test_transient_forbidden_action_is_a_disturbance(self) -> None:
        after = {
            "tabs": {
                "target": {"playback": "paused"},
                "other": {"playback": "playing"},
            }
        }
        result = evaluate(
            self.task,
            self.before,
            after,
            3,
            action_paths=[
                "tabs.target.playback",
                "tabs.other.playback",
                "tabs.other.playback",
            ],
        )
        self.assertTrue(result["exact_success"])
        self.assertFalse(result["disturbance_free_success"])
        self.assertEqual(["tabs.other.playback"], result["transient_side_effects"])


if __name__ == "__main__":
    unittest.main()
