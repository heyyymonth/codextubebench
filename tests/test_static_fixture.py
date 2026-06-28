import json
import shutil
import subprocess
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
    score_static_trace_file,
    validate_executable_trace,
)


STATIC_DIR = repository_root() / "docs" / "static-fixture"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class StaticFixtureTests(unittest.TestCase):
    def completed_trace(self) -> dict:
        trace = json.loads(
            (STATIC_DIR / "trace-template.json").read_text(encoding="utf-8")
        )
        trace.update(
            {
                "run_id": "static-test-run",
                "benchmark_git_revision": "test-revision",
                "benchmark_git_dirty": False,
                "started_at": "2026-06-23T00:00:00+00:00",
                "ended_at": "2026-06-23T00:00:01+00:00",
                "execution_surface": {
                    "type": "manual",
                    "public_url": "https://example.test/codextubebench/",
                    "fixture_version": "codextubebench-static-fixture.v0.3",
                    "deployment_id": "test-deployment",
                },
                "observations": [
                    {
                        "sequence": 0,
                        "channel": "screenshot",
                        "timestamp": "2026-06-23T00:00:00+00:00",
                    },
                    {
                        "sequence": 1,
                        "channel": "player_state",
                        "timestamp": "2026-06-23T00:00:01+00:00",
                        "details": {
                            "static_trace_completion": True,
                            "initial_playback_states": {
                                "player-a": "paused",
                                "player-b": "playing",
                                "player-c": "paused",
                            },
                            "final_playback_states": {
                                "player-a": "paused",
                                "player-b": "paused",
                                "player-c": "paused",
                            },
                        },
                    },
                ],
                "actions": [{"type": "pause", "player_id": "player-b"}],
                "browser_tool_calls": [
                    {
                        "sequence": 1,
                        "source": "static-browser",
                        "name": "pause",
                        "timestamp": "2026-06-23T00:00:00+00:00",
                    },
                    {
                        "sequence": 2,
                        "source": "static-browser",
                        "name": "verify_final_playback_state",
                        "timestamp": "2026-06-23T00:00:01+00:00",
                    },
                ],
                "verifications": ["final_playback_state"],
            }
        )
        return trace

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
        handoff = (STATIC_DIR / "trace-handoff.js").read_text(encoding="utf-8")
        self.assertIn('id="trace-json"', html)
        self.assertIn('id="select-trace"', html)
        self.assertIn('id="copy-trace"', html)
        self.assertIn('data-testid="research-paper-link"', html)
        self.assertIn("navigator.clipboard.writeText", script)
        self.assertIn("selectTraceText", script)
        self.assertIn("sanitizePublicUrl", script)
        self.assertIn("url.search = \"\";", handoff)
        self.assertNotIn("localStorage", script)
        self.assertNotIn("localStorage", handoff)
        self.assertNotIn("navigator.sendBeacon", script)
        self.assertNotIn("XMLHttpRequest", script)

    def test_static_cockpit_has_stable_no_scroll_controls(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        styles = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
        for element_id in (
            "fixture-ready",
            "fixture-readiness-state",
            "controller-probe",
            "controller-probe-ready-text",
            "controller-probe-task-id",
            "controller-probe-revision",
            "controller-probe-controls-present",
            "controller-probe-trace-present",
            "task-cockpit",
            "task-instruction",
            "player-state-list",
            "pause-playing",
            "final-state-verification",
            "submit-answer",
            "trace-handoff",
            "trace-json",
            "select-trace",
            "copy-trace",
            "download-trace",
            "result-summary",
            "status",
        ):
            self.assertIn(f'id="{element_id}"', html)
        for test_id in (
            "fixture-ready",
            "fixture-readiness-state",
            "controller-probe",
            "controller-probe-ready-text",
            "controller-probe-task-id",
            "controller-probe-revision",
            "controller-probe-controls-present",
            "controller-probe-trace-present",
            "controller-probe-main-link",
            "task-cockpit",
            "task-instruction",
            "player-state-list",
            "pause-playing",
            "final-state-verification",
            "submit-answer",
            "trace-handoff",
            "trace-json",
            "select-trace",
            "copy-trace",
            "download-trace",
            "result-summary",
            "summary-task-id",
            "summary-fixture-revision",
            "summary-initial-states",
            "summary-final-states",
            "summary-action",
            "summary-verification",
            "summary-timestamp",
            "summary-trace-id",
            "status",
        ):
            self.assertIn(f'data-testid="{test_id}"', html)
        self.assertIn('data-initial-viewport-contract="390x600"', html)
        self.assertIn('data-ready="false"', html)
        self.assertIn("@media (max-width: 600px)", styles)
        self.assertIn("@media (max-height: 620px)", styles)
        self.assertIn('body[data-phase="completed"]', styles)
        self.assertIn('body[data-controller-probe="true"]', styles)
        self.assertIn("min-height: 122px", styles)
        self.assertNotIn("position: fixed", styles)

    def test_static_fixture_exposes_readiness_contract(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-testid="fixture-ready"', html)
        self.assertIn('data-testid="fixture-readiness-state"', html)
        self.assertIn("window.CodexTubeBenchStaticReady", script)
        for required in (
            "fixture_id",
            "fixture_version",
            "deployed_revision",
            "task_id",
            "readiness_contract_version",
            "assets_loaded",
            "trace_handoff_ready",
            "scorer_contract_version",
            "initialized_at",
        ):
            self.assertIn(required, script)
        for readiness_check in (
            "task_json_loaded",
            "trace_template_json_loaded",
            "deployment_metadata_json_loaded",
            "app_js_initialized",
            "cockpit_controls_attached",
            "trace_textarea_exists",
            "static_trace_handoff_ready",
            "task_initial_state_rendered",
        ):
            self.assertIn(readiness_check, script)
        self.assertLess(
            script.index("renderCockpitStates();"),
            script.rindex("markFixtureReady()"),
        )

    def test_static_fixture_exposes_lightweight_controller_probe(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        styles = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
        for marker in (
            'data-testid="controller-probe"',
            'data-testid="controller-probe-ready-text"',
            'data-testid="controller-probe-task-id"',
            'data-testid="controller-probe-revision"',
            'data-testid="controller-probe-controls-present"',
            'data-testid="controller-probe-trace-present"',
            "CODEXTUBEBENCH STATIC INITIALIZING",
        ):
            self.assertIn(marker, html)
        self.assertIn('CONTROLLER_PROBE_QUERY_PARAM = "controller_probe"', script)
        self.assertIn("renderControllerProbe(snapshot)", script)
        self.assertIn('document.body.dataset.controllerProbe = "true"', script)
        self.assertIn('body[data-controller-probe="true"] .controller-probe', styles)

    def test_static_fixture_exposes_lightweight_readiness_endpoints(self) -> None:
        ready_txt = (STATIC_DIR / "ready.txt").read_text(encoding="utf-8")
        ready_json = json.loads((STATIC_DIR / "ready.json").read_text(encoding="utf-8"))
        ready_html = (STATIC_DIR / "ready.html").read_text(encoding="utf-8")
        self.assertEqual("CODEXTUBEBENCH_STATIC_READY", ready_txt.splitlines()[0])
        self.assertIn("fixture_id=codextubebench-static-tce-002", ready_txt)
        self.assertIn("fixture_version=codextubebench-static-fixture.v0.3", ready_txt)
        self.assertIn("task_id=TCE-002", ready_txt)
        self.assertIn(
            "readiness_contract_version=codextubebench-static-readiness.v0.1",
            ready_txt,
        )
        self.assertEqual("codextubebench-static-tce-002", ready_json["fixture_id"])
        self.assertEqual("codextubebench-static-fixture.v0.3", ready_json["fixture_version"])
        self.assertEqual("codextubebench-static-readiness.v0.1", ready_json["readiness_contract_version"])
        self.assertEqual("TCE-002", ready_json["task_id"])
        self.assertTrue(ready_json["ready"])
        self.assertIn("deployment-metadata.json", ready_json["required_assets"])
        self.assertIn("CODEXTUBEBENCH STATIC READY", ready_html)
        self.assertIn('data-testid="controller-ready"', ready_html)
        self.assertIn('data-ready="true"', ready_html)
        self.assertIn('data-task-id="TCE-002"', ready_html)
        self.assertIn('data-fixture-version="codextubebench-static-fixture.v0.3"', ready_html)
        self.assertIn('data-deployed-revision="unpublished"', ready_html)
        self.assertNotIn("<script", ready_html.lower())
        self.assertNotIn("<link", ready_html.lower())

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
        version = "codextubebench-static-fixture.v0.3"
        self.assertIn(version, script)
        self.assertEqual(version, trace["execution_surface"]["fixture_version"])
        self.assertIn("./styles.css?fixture=v0.3-ready", html)
        self.assertIn("./trace-handoff.js?fixture=v0.3-ready", html)
        self.assertIn("./app.js?fixture=v0.3-ready", html)
        self.assertIn('STATIC_ASSET_REVISION = "v0.3-ready"', script)
        for asset in (
            "task.json",
            "trace-template.json",
            "deployment-metadata.json",
        ):
            self.assertIn(f'fetch(`./{asset}?fixture=${{STATIC_ASSET_REVISION}}`)', script)

    def test_static_trace_template_validates_and_rescores(self) -> None:
        trace = self.completed_trace()
        self.assertEqual([], validate_executable_trace(trace))
        task = next(
            row for row in load_executable_catalog() if row["id"] == "TCE-002"
        )
        evaluated, result = evaluate_executable_trace(task, deepcopy(trace))
        self.assertTrue(evaluated["passed"])
        self.assertTrue(result["passed"])
        self.assertEqual(0, evaluated["side_effects"]["incident_count"])

    def test_static_score_result_passes_and_contains_no_secret_material(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace_path = root / "trace.json"
            result_path = root / "result.json"
            trace_path.write_text(
                json.dumps(self.completed_trace()),
                encoding="utf-8",
            )
            trace_text = trace_path.read_text(encoding="utf-8")
            for forbidden in ("Authorization", "Bearer ", "cookie", "token="):
                self.assertNotIn(forbidden, trace_text)
            result, valid = score_static_trace_file(trace_path, result_path)
            self.assertTrue(valid)
            self.assertTrue(result["passed"])
            self.assertIsNone(result["failure_category"])
            self.assertEqual(
                "codextubebench-static-trace-result.v0.1",
                result["schema_version"],
            )
            text = result_path.read_text(encoding="utf-8")
            for forbidden in ("Authorization", "Bearer ", "cookie", "token="):
                self.assertNotIn(forbidden, text)

    def test_static_score_classifies_valid_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace_path = root / "trace.json"
            result_path = root / "result.json"
            trace = self.completed_trace()
            trace["actions"] = []
            trace_path.write_text(json.dumps(trace), encoding="utf-8")
            result, valid = score_static_trace_file(trace_path, result_path)
            self.assertTrue(valid)
            self.assertFalse(result["passed"])
            self.assertEqual("task_state_failure", result["failure_category"])

    def test_static_score_classifies_missing_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace_path = root / "trace.json"
            result_path = root / "result.json"
            trace = self.completed_trace()
            trace["verifications"] = []
            trace_path.write_text(json.dumps(trace), encoding="utf-8")
            result, valid = score_static_trace_file(trace_path, result_path)
            self.assertTrue(valid)
            self.assertFalse(result["passed"])
            self.assertEqual("verification_failure", result["failure_category"])

    def test_invalid_static_json_writes_failure_result_and_cli_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace_path = root / "trace.json"
            result_path = root / "result.json"
            trace_path.write_text("{not-json", encoding="utf-8")
            completed = subprocess.run(
                [
                    "python3",
                    "-m",
                    "tubebench.cli",
                    "score-static-trace",
                    "--trace",
                    str(trace_path),
                    "--output",
                    str(result_path),
                ],
                cwd=repository_root(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, completed.returncode)
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertFalse(result["valid"])
            self.assertEqual("trace_validation_failure", result["failure_category"])

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for JS runtime tests")
    def test_dependency_free_trace_handoff_javascript(self) -> None:
        completed = subprocess.run(
            ["node", "--test", str(repository_root() / "tests" / "static_trace_handoff.test.js")],
            cwd=repository_root(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

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
                "trace-handoff.js",
                "styles.css",
                "task.json",
                "trace-template.json",
                "deployment-metadata.json",
                "ready.txt",
                "ready.json",
                "ready.html",
            ):
                response = urlopen(f"{base_url}/{asset}")
                self.assertEqual(200, response.status)
                self.assertTrue(response.read())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_public_pages_includes_research_paper_endpoint(self) -> None:
        workflow = (
            repository_root()
            / ".github/workflows/deploy-static-fixture-pages.yml"
        ).read_text(encoding="utf-8")
        paper = (repository_root() / "docs/paper/index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("cp -R docs/paper/. _site/paper/", workflow)
        self.assertIn("CodexTubeBench: Empirical Analysis", paper)
        self.assertIn("Readiness-gated repetition", paper)
        self.assertIn("katex", paper.lower())
        self.assertIn("Exact success placeholder", paper)
        self.assertNotIn("/Users/", paper)


if __name__ == "__main__":
    unittest.main()
