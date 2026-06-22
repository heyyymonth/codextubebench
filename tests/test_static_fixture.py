import json
import tempfile
import threading
import unittest
from copy import deepcopy
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from tubebench.executable import (
    agent_view,
    evaluate_executable_trace,
    load_executable_catalog,
    repository_root,
    validate_executable_trace,
)


STATIC_DIR = repository_root() / "docs" / "static-fixture"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class StaticFixtureTests(unittest.TestCase):
    def test_static_task_is_exact_agent_view_projection(self) -> None:
        task = next(
            row for row in load_executable_catalog() if row["id"] == "TCE-002"
        )
        expected = agent_view(task, task["initial_state"], "gui_native")
        payload = json.loads((STATIC_DIR / "task.json").read_text(encoding="utf-8"))
        self.assertEqual("codextubebench-static-task.v0.1", payload["schema_version"])
        self.assertEqual(expected["task"], payload["task"])
        self.assertEqual(expected["players"], payload["players"])
        self.assertEqual(expected["audit_log"], payload["audit_log"])
        self.assertNotIn("success", payload)
        self.assertNotIn("scripted_run", payload)
        self.assertNotIn("initial_state", payload)

    def test_static_site_has_no_evaluator_credentials_or_backend_routes(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(STATIC_DIR.iterdir())
            if path.is_file()
        )
        for forbidden in (
            "CODEXTUBEBENCH_ORACLE_TOKEN",
            "X-Oracle-Token",
            "/api/",
            "state_predicates",
            "scripted_run",
        ):
            self.assertNotIn(forbidden, text)

    def test_private_trace_handoff_is_post_submission_and_local_only(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="copy-trace"', html)
        self.assertIn("disabled", html)
        self.assertIn("navigator.clipboard.writeText", script)
        self.assertIn(
            'document.querySelector("#copy-trace").disabled = false;',
            script,
        )
        self.assertNotIn("navigator.sendBeacon", script)
        self.assertNotIn("XMLHttpRequest", script)

    def test_static_cockpit_has_stable_no_scroll_controls(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        styles = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
        for element_id in (
            "task-cockpit",
            "task-instruction",
            "player-state-list",
            "pause-playing",
            "final-state-verification",
            "submit-answer",
            "copy-trace",
            "download-trace",
            "status",
        ):
            self.assertIn(f'id="{element_id}"', html)
        for test_id in (
            "task-cockpit",
            "task-instruction",
            "player-state-list",
            "pause-playing",
            "final-state-verification",
            "submit-answer",
            "copy-trace",
            "download-trace",
            "status",
        ):
            self.assertIn(f'data-testid="{test_id}"', html)
        self.assertIn('data-initial-viewport-contract="390x600"', html)
        self.assertIn("@media (max-width: 600px)", styles)
        self.assertIn("@media (max-height: 620px)", styles)
        self.assertNotIn("position: fixed", styles)

    def test_keyboard_shortcuts_are_scoped_away_from_controls(self) -> None:
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn('key === "p" || key === " "', script)
        self.assertIn('key === "v"', script)
        self.assertIn('key === "c"', script)
        self.assertIn("isInteractiveTarget(event.target)", script)
        self.assertIn('document.addEventListener("keydown", handleShortcut)', script)

    def test_static_fixture_version_is_consistent(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        trace = json.loads(
            (STATIC_DIR / "trace-template.json").read_text(encoding="utf-8")
        )
        version = "codextubebench-static-fixture.v0.2"
        self.assertIn(version, script)
        self.assertEqual(version, trace["execution_surface"]["fixture_version"])
        self.assertIn("./styles.css?fixture=v0.2", html)
        self.assertIn("./app.js?fixture=v0.2", html)
        for asset in (
            "task.json",
            "trace-template.json",
            "deployment-metadata.json",
        ):
            self.assertIn(f'fetch("./{asset}?fixture=v0.2")', script)

    def test_static_trace_template_validates_and_rescores(self) -> None:
        trace = json.loads(
            (STATIC_DIR / "trace-template.json").read_text(encoding="utf-8")
        )
        trace.update(
            {
                "run_id": "static-test-run",
                "benchmark_git_revision": "test-revision",
                "benchmark_git_dirty": False,
                "started_at": "2026-06-22T00:00:00+00:00",
                "ended_at": "2026-06-22T00:00:01+00:00",
                "observations": [
                    {
                        "sequence": 0,
                        "channel": "screenshot",
                        "timestamp": "2026-06-22T00:00:00+00:00",
                    }
                ],
                "actions": [{"type": "pause", "player_id": "player-b"}],
                "browser_tool_calls": [
                    {
                        "sequence": 1,
                        "source": "static-browser",
                        "name": "pause",
                        "timestamp": "2026-06-22T00:00:00+00:00",
                    }
                ],
                "verifications": ["final_playback_state"],
            }
        )
        self.assertEqual([], validate_executable_trace(trace))
        task = next(
            row for row in load_executable_catalog() if row["id"] == "TCE-002"
        )
        evaluated, result = evaluate_executable_trace(task, deepcopy(trace))
        self.assertTrue(evaluated["passed"])
        self.assertTrue(result["passed"])
        self.assertEqual(0, evaluated["side_effects"]["incident_count"])

    def test_static_assets_resolve_from_relative_paths(self) -> None:
        handler = lambda *args, **kwargs: QuietStaticHandler(
            *args,
            directory=str(STATIC_DIR),
            **kwargs,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            for asset in (
                "",
                "app.js",
                "styles.css",
                "task.json",
                "trace-template.json",
                "deployment-metadata.json",
            ):
                response = urlopen(f"{base_url}/{asset}")
                self.assertEqual(200, response.status)
                self.assertTrue(response.read())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
