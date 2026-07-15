from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

from tubebench import __version__


ROOT = Path(__file__).resolve().parents[1]

RETIRED_PATHS = (
    "benchmarks/longform_seed",
    "benchmarks/tubeworkflow",
    "configs",
    "skills",
    "src/tubebench/longform_catalog.py",
    "src/tubebench/modes.py",
    "prompts/browser_only.md",
    "schemas/longform_result.schema.json",
    "schemas/longform_task.schema.json",
    "schemas/longform_trace.schema.json",
    "schemas/rubric.schema.json",
    "docs/artifact_contract.md",
    "docs/contributing.md",
    "docs/longform_experiment_framework.md",
    "docs/related_work.md",
    "docs/reproducibility.md",
    "docs/roadmap.md",
    "docs/safety_and_policies.md",
    "docs/setup.md",
    "docs/task_schema.md",
)

LOCAL_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


class RepositoryHygieneTests(unittest.TestCase):
    def test_package_and_project_versions_match(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual("0.2.0", project["project"]["version"])
        self.assertEqual(project["project"]["version"], __version__)

    def test_retired_surfaces_are_absent(self) -> None:
        for relative in RETIRED_PATHS:
            with self.subTest(path=relative):
                self.assertFalse((ROOT / relative).exists())

        retained_text = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in (
                "BENCHMARK_CARD.md",
                "Makefile",
                "src/tubebench/cli.py",
                "docs/methodology.md",
                "docs/limitations.md",
            )
        )
        for retired_name in ("longform_seed", "longform_catalog", "hybrid_enterprise", "validate-longform"):
            with self.subTest(name=retired_name):
                self.assertNotIn(retired_name, retained_text)

    def test_community_files_exist_and_warn_about_private_data(self) -> None:
        paths = (
            ROOT / "CONTRIBUTING.md",
            ROOT / ".github/ISSUE_TEMPLATE/bug_report.md",
            ROOT / ".github/ISSUE_TEMPLATE/benchmark_proposal.md",
        )
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8").lower()
                self.assertIn("credentials", text)
                self.assertIn("cookies", text)
                self.assertIn("private", text)

        proposal = paths[-1].read_text(encoding="utf-8").lower()
        for requirement in (
            "success predicates",
            "protected state",
            "evidence channels",
            "safety",
            "evaluator tests",
        ):
            self.assertIn(requirement, proposal)

    def test_reader_facing_local_links_resolve(self) -> None:
        for relative in ("README.md", "BENCHMARK_CARD.md", "CONTRIBUTING.md"):
            source = ROOT / relative
            text = source.read_text(encoding="utf-8")
            for target in LOCAL_LINK.findall(text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path_text = target.split("#", 1)[0]
                if not path_text:
                    continue
                resolved = (source.parent / path_text).resolve()
                with self.subTest(source=relative, target=target):
                    self.assertTrue(resolved.exists())


if __name__ == "__main__":
    unittest.main()
