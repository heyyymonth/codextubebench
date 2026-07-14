import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
CI_WORKFLOW = WORKFLOW_DIR / "ci.yml"
PAGES_WORKFLOW = WORKFLOW_DIR / "deploy-static-fixture-pages.yml"

MINIMUM_ACTION_MAJORS = {
    "actions/checkout": 7,
    "actions/configure-pages": 6,
    "actions/upload-pages-artifact": 5,
    "actions/deploy-pages": 5,
}
PINNED_ACTION = re.compile(
    r"uses:\s+(actions/[A-Za-z0-9_.-]+)@([0-9a-f]{40})\s+#\s+v(\d+)\."
)


class GitHubWorkflowTests(unittest.TestCase):
    def test_first_party_actions_are_sha_pinned_and_node24_compatible(self) -> None:
        seen: dict[str, list[int]] = {}
        for workflow in sorted(WORKFLOW_DIR.glob("*.yml")):
            for line_number, line in enumerate(
                workflow.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if "uses: actions/" not in line:
                    continue
                match = PINNED_ACTION.search(line)
                self.assertIsNotNone(
                    match,
                    f"{workflow.name}:{line_number} must use a 40-character SHA "
                    "with a release comment",
                )
                action, _, major = match.groups()
                seen.setdefault(action, []).append(int(major))

        self.assertEqual(set(MINIMUM_ACTION_MAJORS), set(seen))
        for action, majors in seen.items():
            minimum = MINIMUM_ACTION_MAJORS[action]
            self.assertTrue(
                all(major >= minimum for major in majors),
                f"{action} must remain on major version {minimum} or newer",
            )

    def test_workflows_share_the_public_check_gate(self) -> None:
        ci = CI_WORKFLOW.read_text(encoding="utf-8")
        pages = PAGES_WORKFLOW.read_text(encoding="utf-8")
        for workflow in (ci, pages):
            self.assertEqual(1, workflow.count("run: make check"))
            self.assertNotIn("make test validate release-check", workflow)
            self.assertNotIn("scripts/validate_paper_artifact.py", workflow)

    def test_pages_deployment_remains_manual(self) -> None:
        pages = PAGES_WORKFLOW.read_text(encoding="utf-8")
        trigger_block = pages.partition("permissions:")[0]
        self.assertIn("workflow_dispatch:", trigger_block)
        self.assertNotIn("pull_request:", trigger_block)
        self.assertNotIn("push:", trigger_block)

    def test_dependabot_tracks_github_action_updates_weekly(self) -> None:
        config = (ROOT / ".github" / "dependabot.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("package-ecosystem: github-actions", config)
        self.assertIn('directory: "/"', config)
        self.assertIn("interval: weekly", config)


if __name__ == "__main__":
    unittest.main()
