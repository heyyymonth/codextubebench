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
