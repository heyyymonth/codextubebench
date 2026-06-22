import unittest
from copy import deepcopy

from tubebench.live_youtube import (
    load_live_youtube_catalog,
    validate_live_youtube_catalog,
    validate_live_youtube_trace,
)


class LiveYouTubeCatalogTests(unittest.TestCase):
    def test_catalog_has_required_category_coverage(self) -> None:
        tasks = load_live_youtube_catalog()
        self.assertEqual(12, len(tasks))
        self.assertEqual([], validate_live_youtube_catalog(tasks))

    def test_account_mutating_action_is_not_allowed(self) -> None:
        prohibited = {"like", "dislike", "subscribe", "comment", "save", "live_chat"}
        for task in load_live_youtube_catalog():
            self.assertTrue(prohibited <= set(task["forbidden_actions"]))

    def test_invalid_live_trace_channel_is_rejected(self) -> None:
        trace = {
            "schema_version": "live-youtube-trace.v0.1",
            "run_id": "example",
            "task_id": "LYT-001",
            "task_revision": 1,
            "track": "live_youtube_v0",
            "category": "long_form",
            "mode": "instrumented_browser",
            "agent": "codex",
            "url": "https://www.youtube.com/watch?v=example",
            "started_at": "2026-06-21T00:00:00Z",
            "ended_at": "2026-06-21T00:01:00Z",
            "benchmark_git_revision": "example",
            "benchmark_git_dirty": True,
            "availability": {"status": "available"},
            "initial_tabs": [],
            "initial_media_state": {},
            "observations": [],
            "screenshots": [],
            "actions": [],
            "browser_tool_calls": [],
            "channels_used": ["private_api"],
            "watched_intervals": [],
            "final_answer": {},
            "final_tabs": [],
            "final_media_state": {},
            "verifications": [],
            "side_effects": {},
            "metrics": {},
            "passed": False,
            "failure_type": "tool_runtime_limitation",
            "errors": [],
            "qualitative_notes": {},
        }
        self.assertTrue(validate_live_youtube_trace(trace))

    def test_catalog_rejects_live_url_shortfall(self) -> None:
        tasks = deepcopy(load_live_youtube_catalog())
        for task in tasks:
            if task["category"] == "live_stream":
                task["url"] = "https://www.youtube.com/watch?v=one-live-url"
        self.assertTrue(
            any(
                "two live-stream URLs" in error
                for error in validate_live_youtube_catalog(tasks)
            )
        )

    def test_granular_trace_detects_criterion_score_drift(self) -> None:
        trace = {
            "schema_version": "live-youtube-trace.v0.2",
            "run_id": "example",
            "experiment_id": "LYT-002-localization-r1",
            "attempt_index": 1,
            "task_id": "LYT-002",
            "task_revision": 1,
            "track": "live_youtube_v0",
            "category": "long_form",
            "mode": "instrumented_browser",
            "agent": "codex",
            "url": "https://www.youtube.com/watch?v=example",
            "started_at": "2026-06-21T00:00:00Z",
            "ended_at": "2026-06-21T00:01:00Z",
            "benchmark_git_revision": "7ca8541",
            "benchmark_git_dirty": True,
            "availability": {
                "status": "available",
                "checked_at": "2026-06-21T00:00:00Z",
                "ad_observed": False,
                "sign_in_required": False,
            },
            "initial_tabs": [],
            "initial_media_state": {},
            "state_snapshots": [
                {"snapshot_id": "state-1", "phase": "initial"},
                {"snapshot_id": "state-2", "phase": "final"},
            ],
            "observations": [
                {
                    "observation_id": "obs-1",
                    "channel": "youtube_ui",
                    "confidence": 1.0,
                    "supports_criteria": ["timestamp"],
                }
            ],
            "screenshots": [],
            "actions": [],
            "browser_tool_calls": [
                {"tool_call_id": "tool-1", "operation": "domSnapshot"}
            ],
            "channels_used": ["youtube_ui"],
            "watched_intervals": [],
            "final_answer": {},
            "final_tabs": [],
            "final_media_state": {},
            "criteria_results": [
                {
                    "criterion_id": "timestamp",
                    "required": True,
                    "weight": 1,
                    "status": "partial",
                    "score": 0.5,
                    "evidence_observation_ids": ["obs-1"],
                    "failure_ids": [],
                }
            ],
            "verifications": [],
            "side_effects": {
                "incident_count": 0,
                "incidents": [],
            },
            "metrics": {},
            "outcome": {
                "status": "partial",
                "criterion_score": 1.0,
                "required_criteria_passed": False,
            },
            "passed": False,
            "failure_type": "none",
            "failures": [],
            "errors": [],
            "qualitative_notes": {},
        }
        errors = validate_live_youtube_trace(trace)
        self.assertTrue(any("criterion_score" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
