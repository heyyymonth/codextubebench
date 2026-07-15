import json
import tempfile
import threading
import unittest
from copy import deepcopy
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tubebench.executable import (
    TRACE_SCHEMA_VERSION_V2,
    FixtureSession,
    agent_view,
    load_executable_catalog,
    repository_root,
    run_executable_suite,
    validate_executable_catalog,
    validate_executable_trace,
)
from tubebench.fixture_server import FixtureApplication, ThreadingHTTPServer, make_handler


class ExecutableCatalogTests(unittest.TestCase):
    def test_catalog_contains_twelve_runnable_tasks(self) -> None:
        tasks = load_executable_catalog()
        self.assertEqual(12, len(tasks))
        self.assertEqual([], validate_executable_catalog(tasks))

    def test_gui_view_hides_transcripts_and_oracle_answers(self) -> None:
        task = load_executable_catalog()[7]
        view = agent_view(task, task["initial_state"], "gui_native")
        self.assertNotIn("transcripts", view)
        self.assertNotIn("success", json.dumps(view))

    def test_checked_in_trace_example_matches_the_trace_contract(self) -> None:
        trace = json.loads(
            (repository_root() / "examples" / "executable_trace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual([], validate_executable_trace(trace))


class ExecutableRunnerTests(unittest.TestCase):
    def test_v2_noop_without_attributable_progress_is_failed(self) -> None:
        task = load_executable_catalog()[1]
        session = FixtureSession(
            task,
            "instrumented_browser",
            "test-agent",
            trace_version=TRACE_SCHEMA_VERSION_V2,
        )
        session.view()
        session.submit(None, [])
        trace = session.trace()
        self.assertEqual("failed", trace["outcome"]["status"])
        self.assertFalse(trace["outcome"]["task_positive_progress"])
        self.assertEqual(0, trace["dimensions"]["step_execution"]["total"])

    def test_v2_granular_trace_reports_dimensions_without_composite(self) -> None:
        task = load_executable_catalog()[1]
        session = FixtureSession(
            task,
            "instrumented_browser",
            "test-agent",
            benchmark_revision="a" * 40,
            benchmark_dirty=False,
            trace_version=TRACE_SCHEMA_VERSION_V2,
        )
        session.view()
        session.apply({"type": "pause", "player_id": "player-b"})
        session.submit(None, ["final_playback_state"])
        trace = session.trace()
        self.assertEqual([], validate_executable_trace(trace))
        self.assertEqual("completed", trace["outcome"]["status"])
        self.assertEqual(1.0, trace["dimensions"]["state_correctness"]["rate"])
        self.assertEqual(1.0, trace["dimensions"]["verification"]["rate"])
        self.assertGreater(trace["dimensions"]["step_execution"]["useful"], 0)
        self.assertEqual(2, trace["dimensions"]["step_execution"]["total"])
        self.assertEqual(1.0, trace["dimensions"]["efficiency"]["action_reference_ratio"])
        self.assertTrue(trace["step_results"][-1]["verification_completed"])
        self.assertNotIn("criterion_score", json.dumps(trace["dimensions"]))
        self.assertNotIn("weighted_efficiency", trace["metrics"])

    def test_v2_wrong_answer_with_grounded_observation_is_partial(self) -> None:
        task = load_executable_catalog()[8]
        session = FixtureSession(
            task,
            "instrumented_browser",
            "test-agent",
            trace_version=TRACE_SCHEMA_VERSION_V2,
        )
        session.view()
        session.apply(
            {
                "type": "observe",
                "channel": "transcript",
                "media_id": "systems-lecture",
                "cue_id": "sys-components",
            }
        )
        session.submit("planner only", ["transcript_cue_checked"])
        trace = session.trace()
        self.assertEqual("partial", trace["outcome"]["status"])
        self.assertLess(trace["dimensions"]["answer_correctness"]["rate"], 1.0)
        self.assertEqual(1.0, trace["dimensions"]["evidence_grounding"]["rate"])

    def test_v2_invalid_action_can_record_a_recovery_without_hiding_error(self) -> None:
        task = load_executable_catalog()[1]
        session = FixtureSession(
            task,
            "instrumented_browser",
            "test-agent",
            trace_version=TRACE_SCHEMA_VERSION_V2,
        )
        session.view()
        with self.assertRaisesRegex(ValueError, "unknown player"):
            session.apply({"type": "pause", "player_id": "missing-player"})
        session.apply({"type": "pause", "player_id": "player-b"})
        session.submit(None, ["final_playback_state"])
        trace = session.trace()
        self.assertFalse(trace["trace_valid"])
        self.assertEqual("invalid", trace["outcome"]["status"])
        self.assertEqual(1, trace["dimensions"]["step_execution"]["invalid"])
        self.assertEqual(1, trace["dimensions"]["recovery"]["succeeded"])
        self.assertTrue(trace["errors"])

    def test_scripted_baseline_passes_and_emits_valid_traces(self) -> None:
        tasks = load_executable_catalog()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = run_executable_suite(
                tasks,
                agent="scripted",
                seed=1,
                output=output,
            )
            self.assertEqual(12, manifest["passed"])
            trace = json.loads(
                (output / "TCE-010" / "trace.json").read_text(encoding="utf-8")
            )
            self.assertEqual([], validate_executable_trace(trace))
            watched = trace["watched_intervals"][0]
            self.assertEqual(
                8.0,
                watched["end_seconds"] - watched["start_seconds"],
            )
            metrics = trace["metrics"]
            self.assertEqual(
                len(trace["browser_tool_calls"]),
                metrics["browser_tool_call_count"],
            )
            self.assertEqual(8.0, metrics["watch_time_seconds"])
            self.assertEqual(
                trace["side_effects"]["incident_count"],
                metrics["side_effect_incident_count"],
            )
            self.assertIsNone(metrics["failure_category"])

            restoration_trace = json.loads(
                (output / "TCE-004" / "trace.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                1.0,
                restoration_trace["metrics"]["state_restoration_score"],
            )

    def test_noop_baseline_does_not_masquerade_as_success(self) -> None:
        tasks = load_executable_catalog()
        with tempfile.TemporaryDirectory() as directory:
            manifest = run_executable_suite(
                tasks,
                agent="noop",
                seed=1,
                output=Path(directory),
            )
            self.assertLess(manifest["passed"], 12)

    def test_transient_or_restored_forbidden_change_is_an_incident(self) -> None:
        task = deepcopy(load_executable_catalog()[6])
        session = FixtureSession(task, "instrumented_browser", "test-agent")
        session.apply(
            {"type": "set_muted", "player_id": "player-b", "value": False}
        )
        session.apply(
            {"type": "set_muted", "player_id": "player-b", "value": True}
        )
        trace = session.trace()
        self.assertFalse(trace["passed"])
        self.assertGreaterEqual(trace["side_effects"]["incident_count"], 1)
        self.assertTrue(
            any(
                incident["restored_in_final_state"]
                for incident in trace["side_effects"]["incidents"]
            )
        )

    def test_gui_mode_rejects_instrumented_channel_use(self) -> None:
        task = load_executable_catalog()[0]
        session = FixtureSession(task, "gui_native", "test-agent")
        with self.assertRaisesRegex(ValueError, "does not permit channel"):
            session.apply(
                {
                    "type": "observe",
                    "channel": "dom_player_state",
                }
            )


class FixtureServerTests(unittest.TestCase):
    def test_oracle_endpoint_requires_evaluator_token(self) -> None:
        application = FixtureApplication(oracle_token="test-oracle-token")
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(application))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            request = Request(
                f"{base_url}/api/sessions",
                data=json.dumps(
                    {
                        "task_id": "TCE-002",
                        "mode": "gui_native",
                        "agent": "test-agent",
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            created = json.loads(urlopen(request).read())
            session_id = created["session_id"]
            with self.assertRaises(HTTPError) as context:
                urlopen(f"{base_url}/api/sessions/{session_id}/oracle")
            self.assertEqual(403, context.exception.code)
            oracle_request = Request(
                f"{base_url}/api/sessions/{session_id}/oracle",
                headers={"X-Oracle-Token": "test-oracle-token"},
            )
            oracle = json.loads(urlopen(oracle_request).read())
            self.assertEqual("playing", oracle["players"]["player-b"]["playback"])
            action_request = Request(
                f"{base_url}/api/sessions/{session_id}/actions",
                data=json.dumps(
                    {"type": "pause", "player_id": "player-b"}
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urlopen(action_request).read()
            reset_request = Request(
                f"{base_url}/api/sessions/{session_id}/reset",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            reset_view = json.loads(urlopen(reset_request).read())
            self.assertEqual(
                "playing",
                reset_view["players"]["player-b"]["playback"],
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
