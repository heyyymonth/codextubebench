import tempfile
import unittest
from pathlib import Path

from tubebench.catalog import load_catalog
from tubebench.io import read_jsonl
from tubebench.runner import run_suite, summarize_rows


class RunnerTests(unittest.TestCase):
    def test_perfect_and_reckless_agents_separate_success_from_safety(self) -> None:
        tasks = load_catalog()[:2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_suite(tasks, "mock-perfect", 1, root / "perfect")
            manifest = (root / "perfect" / "manifest.json").read_text(encoding="utf-8")
            self.assertIn('"benchmark_git_revision"', manifest)
            perfect = summarize_rows(read_jsonl(root / "perfect/results.jsonl"))
            self.assertEqual(1.0, perfect["disturbance_free_success_rate"])

            run_suite(tasks, "mock-reckless", 1, root / "reckless")
            reckless = summarize_rows(read_jsonl(root / "reckless/results.jsonl"))
            self.assertEqual(1.0, reckless["exact_success_rate"])
            self.assertEqual(0.0, reckless["disturbance_free_success_rate"])

            run_suite(tasks, "mock-transient", 1, root / "transient")
            transient = summarize_rows(read_jsonl(root / "transient/results.jsonl"))
            self.assertEqual(1.0, transient["exact_success_rate"])
            self.assertEqual(0.0, transient["disturbance_free_success_rate"])


if __name__ == "__main__":
    unittest.main()
