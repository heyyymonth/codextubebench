import unittest
from copy import deepcopy

from tubebench.live_public_video import (
    SITE_COUNTS,
    load_live_public_video_catalog,
    validate_live_public_video_catalog,
    validate_live_public_video_trace,
)


def valid_trace() -> dict:
    return {
        "schema_version": "live-public-video-trace.v0.1",
        "run_id": "lpv-pilot-v0",
        "attempt_id": "lpv-pilot-v0__LPV-001__seed-11",
        "task_id": "LPV-001",
        "task_revision": 1,
        "track": "live_public_video_v0",
        "site": "youtube",
        "task_family": "metadata_inspection",
        "mode": "instrumented_browser",
        "agent": "codex-in-app-browser",
        "url": "https://www.youtube.com/watch?v=alfdI7S6wCY",
        "started_at": "2026-06-30T00:00:00Z",
        "ended_at": "2026-06-30T00:01:00Z",
        "benchmark_git_revision": "example",
        "benchmark_git_dirty": False,
        "availability": {"status": "available"},
        "page_refs": [
            {
                "page_ref_id": "page-1",
                "url": "https://www.youtube.com/watch?v=alfdI7S6wCY",
                "label": "primary video page",
            }
        ],
        "screenshots": [
            {
                "screenshot_id": "shot-1",
                "path": "screenshots/initial.png",
                "description": "visible title and player area",
            }
        ],
        "observations": [
            {
                "observation_id": "obs-1",
                "confidence": 1.0,
                "visible_text_snippet": "Example lecture title",
                "screenshot_refs": ["shot-1"],
                "page_refs": ["page-1"],
            }
        ],
        "browser_tool_calls": [
            {"tool_call_id": "tool-1", "operation": "screenshot"}
        ],
        "actions": [
            {"action_id": "action-1", "action_type": "capture_screenshot"}
        ],
        "watched_intervals": [],
        "criteria_results": [
            {
                "criterion_id": "metadata",
                "required": True,
                "weight": 1,
                "status": "pass",
                "score": 1.0,
                "evidence_observation_ids": ["obs-1"],
                "failure_ids": [],
                "unsupported_claim_count": 0,
            }
        ],
        "final_answer": {"summary": "metadata reported"},
        "final_verification": {
            "checks": [
                {
                    "criterion_id": "metadata",
                    "evidence_observation_ids": ["obs-1"],
                }
            ]
        },
        "failures": [],
        "recovery_attempts": [],
        "side_effects": {"incident_count": 0, "incidents": []},
        "metrics": {
            "browser_tool_call_count": 1,
            "watched_seconds": 0,
            "screenshot_coverage": 1.0,
        },
        "outcome": {
            "status": "completed",
            "retained_slot": True,
            "criterion_score": 1.0,
            "required_criteria_passed": True,
            "unsupported_claim_count": 0,
        },
        "errors": [],
        "qualitative_notes": {},
    }


def valid_trace_v2() -> dict:
    trace = deepcopy(valid_trace())
    trace.update(
        {
            "schema_version": "live-public-video-trace.v0.2",
            "run_id": "live-public-video-retained-v1",
            "campaign_id": "live-public-video-retained-v1",
            "attempt_id": "live-public-video-retained-v1__LPV-001__seed-17",
            "seed": 17,
            "benchmark_git_revision": "1" * 40,
            "lab_git_revision": "2" * 40,
            "lab_git_dirty": False,
            "manifest_digest": "3" * 64,
            "config_digest": "4" * 64,
            "catalog_digest": "5" * 64,
            "prompt_digest": "6" * 64,
            "runtime": {
                "codex_identifier": "codex-in-app-browser",
                "browser_name": "in-app-browser",
                "browser_version": "1",
                "viewport_width": 1440,
                "viewport_height": 900,
            },
        }
    )
    return trace


class LivePublicVideoCatalogTests(unittest.TestCase):
    def test_repository_catalog_validates(self) -> None:
        tasks = load_live_public_video_catalog()
        self.assertEqual(sum(SITE_COUNTS.values()), len(tasks))
        self.assertEqual([], validate_live_public_video_catalog(tasks))

    def test_catalog_has_expected_site_counts(self) -> None:
        tasks = load_live_public_video_catalog()
        counts = {site: 0 for site in SITE_COUNTS}
        for task in tasks:
            counts[task["site"]] += 1
        self.assertEqual(SITE_COUNTS, counts)

    def test_public_mutating_allowed_action_is_rejected(self) -> None:
        tasks = deepcopy(load_live_public_video_catalog())
        tasks[0]["allowed_actions"].append("seek")
        self.assertTrue(
            any(
                "allowed_actions must be unique read-only actions" in error
                for error in validate_live_public_video_catalog(tasks)
            )
        )

    def test_missing_required_forbidden_action_is_rejected(self) -> None:
        tasks = deepcopy(load_live_public_video_catalog())
        tasks[0]["forbidden_actions"].remove("download")
        self.assertTrue(
            any(
                "forbidden_actions missing required actions" in error
                for error in validate_live_public_video_catalog(tasks)
            )
        )


class LivePublicVideoTraceTests(unittest.TestCase):
    def test_valid_trace_passes(self) -> None:
        self.assertEqual([], validate_live_public_video_trace(valid_trace()))

    def test_valid_v2_trace_passes(self) -> None:
        self.assertEqual([], validate_live_public_video_trace(valid_trace_v2()))

    def test_v2_trace_requires_clean_pinned_revisions(self) -> None:
        trace = valid_trace_v2()
        trace["benchmark_git_dirty"] = True
        self.assertTrue(
            any(
                "benchmark_git_dirty must be false" in error
                for error in validate_live_public_video_trace(trace)
            )
        )

    def test_v2_pre_capture_failure_may_have_no_screenshot(self) -> None:
        trace = valid_trace_v2()
        trace["observations"] = []
        trace["screenshots"] = []
        trace["browser_tool_calls"] = []
        trace["actions"] = []
        trace["criteria_results"][0].update(
            {
                "status": "blocked",
                "score": 0.0,
                "evidence_observation_ids": [],
                "failure_ids": ["failure-1"],
            }
        )
        trace["final_verification"] = {"checks": []}
        trace["failures"] = [
            {
                "failure_id": "failure-1",
                "type": "trace_capture_failure",
                "stage": "capture",
                "related_action_id": None,
                "related_tool_call_id": None,
                "evidence_observation_ids": [],
            }
        ]
        trace["outcome"].update(
            {
                "status": "invalid",
                "criterion_score": 0.0,
                "required_criteria_passed": False,
            }
        )
        self.assertEqual([], validate_live_public_video_trace(trace))

    def test_missing_screenshot_is_rejected(self) -> None:
        trace = valid_trace()
        trace["screenshots"] = []
        self.assertTrue(
            any(
                "screenshots must contain" in error
                for error in validate_live_public_video_trace(trace)
            )
        )

    def test_sensitive_raw_fields_are_rejected(self) -> None:
        trace = valid_trace()
        trace["browser_profile"] = "private-profile-placeholder"
        self.assertTrue(
            any(
                "forbidden raw browser/account fields" in error
                for error in validate_live_public_video_trace(trace)
            )
        )

    def test_unsupported_claim_score_mismatch_is_rejected(self) -> None:
        trace = valid_trace()
        trace["criteria_results"][0]["unsupported_claim_count"] = 1
        self.assertTrue(
            any(
                "unsupported_claim_count does not match" in error
                for error in validate_live_public_video_trace(trace)
            )
        )


if __name__ == "__main__":
    unittest.main()
