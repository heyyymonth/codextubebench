from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json

TASK_SCHEMA_VERSION = "live-youtube-task.v0.1"
TRACE_SCHEMA_VERSION = "live-youtube-trace.v0.2"
LEGACY_TRACE_SCHEMA_VERSION = "live-youtube-trace.v0.1"
TRACK = "live_youtube_v0"

MODES = {"gui_native", "ui_assisted", "instrumented_browser"}
CATEGORIES = {"long_form", "live_stream", "long_music"}
EVALUATION_TYPES = {
    "exact_state",
    "timestamp_tolerance",
    "qualitative_evidence",
    "side_effect_check",
    "transcript_presence",
    "live_state_check",
}
VOLATILITY_LEVELS = {"low", "medium", "high"}
CHANNEL_LABELS = {
    "transcript",
    "visual",
    "dom_player_state",
    "youtube_ui",
    "mixed",
    "none",
}
FAILURE_TYPES = {
    "none",
    "perception",
    "grounding",
    "youtube_ui_instability",
    "transcript_unavailable",
    "live_state_volatility",
    "verification_failure",
    "side_effect",
    "over_observation",
    "under_observation",
    "tool_runtime_limitation",
    "ad_blocked",
    "candidate_unavailable",
}
OUTCOME_STATUSES = {"completed", "partial", "failed", "blocked", "invalid"}
CRITERION_STATUSES = {"pass", "partial", "fail", "blocked", "not_applicable"}
FAILURE_STAGES = {
    "availability",
    "perception",
    "grounding",
    "planning",
    "action",
    "verification",
    "restoration",
    "runtime",
    "evaluation",
}

REQUIRED_TASK_FIELDS = {
    "schema_version",
    "task_id",
    "track",
    "revision",
    "category",
    "url",
    "title_expected_optional",
    "channel_expected_optional",
    "duration_expected_optional",
    "task_prompt",
    "allowed_modes",
    "allowed_tools",
    "forbidden_actions",
    "side_effect_policy",
    "expected_observations",
    "success_criteria",
    "verification_requirements",
    "volatility_level",
    "reproducibility_notes",
    "trace_requirements",
    "human_reference_notes",
    "evaluation_type",
    "candidate_metadata",
}

REQUIRED_TRACE_FIELDS = {
    "schema_version",
    "run_id",
    "task_id",
    "task_revision",
    "track",
    "category",
    "mode",
    "agent",
    "url",
    "started_at",
    "ended_at",
    "benchmark_git_revision",
    "benchmark_git_dirty",
    "availability",
    "initial_tabs",
    "initial_media_state",
    "observations",
    "screenshots",
    "actions",
    "browser_tool_calls",
    "channels_used",
    "watched_intervals",
    "final_answer",
    "final_tabs",
    "final_media_state",
    "verifications",
    "side_effects",
    "metrics",
    "passed",
    "failure_type",
    "errors",
    "qualitative_notes",
}


def default_live_youtube_catalog_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "benchmarks"
        / TRACK
        / "tasks"
        / "catalog.json"
    )


def load_live_youtube_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    value = read_json(path or default_live_youtube_catalog_path())
    if not isinstance(value, list):
        raise ValueError("live YouTube catalog root must be a JSON array")
    return value


def validate_live_youtube_catalog(tasks: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    candidate_urls: dict[str, set[str]] = {
        "long_form": set(),
        "live_stream": set(),
        "long_music": set(),
    }
    for index, task in enumerate(tasks):
        label = task.get("task_id", f"index {index}")
        missing = sorted(REQUIRED_TASK_FIELDS - task.keys())
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
            continue
        if task["schema_version"] != TASK_SCHEMA_VERSION:
            errors.append(f"{label}: unsupported schema_version")
        if task["track"] != TRACK:
            errors.append(f"{label}: track must be {TRACK}")
        task_id = task["task_id"]
        if not isinstance(task_id, str) or not task_id.startswith("LYT-"):
            errors.append(f"{label}: task_id must start with LYT-")
        elif task_id in seen:
            errors.append(f"{label}: duplicate task id")
        seen.add(task_id)
        if not isinstance(task["revision"], int) or task["revision"] < 1:
            errors.append(f"{label}: revision must be a positive integer")
        category = task["category"]
        if category not in CATEGORIES:
            errors.append(f"{label}: invalid category")
        url = task["url"]
        if not isinstance(url, str) or not url.startswith(
            ("https://www.youtube.com/watch?", "https://youtu.be/")
        ):
            errors.append(f"{label}: url must be a public YouTube watch URL")
        elif category in candidate_urls:
            candidate_urls[category].add(url)
        modes = task["allowed_modes"]
        if (
            not isinstance(modes, list)
            or not modes
            or set(modes) - MODES
            or len(set(modes)) != len(modes)
        ):
            errors.append(f"{label}: allowed_modes contains an invalid mode")
        for field in (
            "allowed_tools",
            "forbidden_actions",
            "expected_observations",
            "success_criteria",
            "verification_requirements",
            "trace_requirements",
        ):
            if not isinstance(task[field], list):
                errors.append(f"{label}: {field} must be a list")
        if task["evaluation_type"] not in EVALUATION_TYPES:
            errors.append(f"{label}: invalid evaluation_type")
        if task["volatility_level"] not in VOLATILITY_LEVELS:
            errors.append(f"{label}: invalid volatility_level")
        duration = task["duration_expected_optional"]
        if duration is not None and (
            not isinstance(duration, (int, float)) or duration <= 0
        ):
            errors.append(
                f"{label}: duration_expected_optional must be positive or null"
            )
        metadata = task["candidate_metadata"]
        if not isinstance(metadata, dict):
            errors.append(f"{label}: candidate_metadata must be an object")
        else:
            if not isinstance(metadata.get("verified_at"), str):
                errors.append(f"{label}: candidate_metadata.verified_at is required")
            if metadata.get("access") not in {
                "public",
                "public_volatile",
                "unavailable",
            }:
                errors.append(f"{label}: candidate_metadata.access is invalid")
        if not isinstance(task["side_effect_policy"], dict):
            errors.append(f"{label}: side_effect_policy must be an object")

    if not 10 <= len(tasks) <= 15:
        errors.append(f"live YouTube pilot catalog must contain 10-15 tasks; found {len(tasks)}")
    if len(candidate_urls["long_form"]) < 5:
        errors.append("live YouTube catalog requires at least five long-form URLs")
    if len(candidate_urls["long_music"]) < 3:
        errors.append("live YouTube catalog requires at least three long-music URLs")
    if len(candidate_urls["live_stream"]) < 2:
        errors.append("live YouTube catalog requires at least two live-stream URLs")
    return errors


def validate_live_youtube_trace(trace: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TRACE_FIELDS - trace.keys())
    if missing:
        errors.append(f"trace missing fields: {', '.join(missing)}")
        return errors
    schema_version = trace["schema_version"]
    if schema_version not in {TRACE_SCHEMA_VERSION, LEGACY_TRACE_SCHEMA_VERSION}:
        errors.append("trace has unsupported schema_version")
    if trace["track"] != TRACK:
        errors.append(f"trace.track must be {TRACK}")
    if trace["category"] not in CATEGORIES:
        errors.append("trace has invalid category")
    if trace["mode"] not in MODES:
        errors.append("trace has invalid mode")
    if trace["failure_type"] not in FAILURE_TYPES:
        errors.append("trace has invalid failure_type")
    availability = trace["availability"]
    if not isinstance(availability, dict) or availability.get("status") not in {
        "available",
        "volatile",
        "blocked",
        "unavailable",
    }:
        errors.append("trace.availability.status is invalid")
    for field in (
        "initial_tabs",
        "observations",
        "screenshots",
        "actions",
        "browser_tool_calls",
        "channels_used",
        "watched_intervals",
        "final_tabs",
        "verifications",
        "errors",
    ):
        if not isinstance(trace[field], list):
            errors.append(f"trace.{field} must be a list")
    if set(trace["channels_used"]) - CHANNEL_LABELS:
        errors.append("trace.channels_used contains an invalid channel")
    if not isinstance(trace["side_effects"], dict):
        errors.append("trace.side_effects must be an object")
    if not isinstance(trace["metrics"], dict):
        errors.append("trace.metrics must be an object")
    if not isinstance(trace["qualitative_notes"], dict):
        errors.append("trace.qualitative_notes must be an object")
    if schema_version == TRACE_SCHEMA_VERSION:
        errors.extend(_validate_v02_trace(trace))
    return errors


def _validate_v02_trace(trace: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "experiment_id",
        "attempt_index",
        "state_snapshots",
        "criteria_results",
        "outcome",
        "failures",
    }
    missing = sorted(required - trace.keys())
    if missing:
        return [f"trace missing v0.2 fields: {', '.join(missing)}"]
    if not isinstance(trace["experiment_id"], str) or not trace["experiment_id"]:
        errors.append("trace.experiment_id must be a non-empty string")
    if not isinstance(trace["attempt_index"], int) or trace["attempt_index"] < 1:
        errors.append("trace.attempt_index must be a positive integer")

    observations = trace["observations"]
    if not observations:
        errors.append("trace.observations must not be empty in v0.2")
    observation_ids = _validate_id_rows(
        observations,
        id_field="observation_id",
        label="trace.observations",
        errors=errors,
    )
    for row in observations:
        if not isinstance(row, dict):
            continue
        if row.get("channel") not in CHANNEL_LABELS:
            errors.append("trace.observations contains an invalid channel")
        confidence = row.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append("trace.observations confidence must be between 0 and 1")
        if not isinstance(row.get("supports_criteria"), list):
            errors.append("trace.observations supports_criteria must be a list")

    action_ids = _validate_id_rows(
        trace["actions"],
        id_field="action_id",
        label="trace.actions",
        errors=errors,
    )
    tool_call_ids = _validate_id_rows(
        trace["browser_tool_calls"],
        id_field="tool_call_id",
        label="trace.browser_tool_calls",
        errors=errors,
    )
    if not tool_call_ids:
        errors.append("trace.browser_tool_calls must not be empty in v0.2")
    failure_ids = _validate_id_rows(
        trace["failures"],
        id_field="failure_id",
        label="trace.failures",
        errors=errors,
    )
    criterion_ids = _validate_id_rows(
        trace["criteria_results"],
        id_field="criterion_id",
        label="trace.criteria_results",
        errors=errors,
    )

    for row in trace["criteria_results"]:
        if not isinstance(row, dict):
            continue
        if row.get("status") not in CRITERION_STATUSES:
            errors.append("trace.criteria_results contains an invalid status")
        score = row.get("score")
        if not isinstance(score, (int, float)) or not 0 <= score <= 1:
            errors.append("trace.criteria_results score must be between 0 and 1")
        elif row.get("status") == "pass" and score != 1:
            errors.append("passing criteria must have score 1")
        elif row.get("status") in {"fail", "blocked"} and score != 0:
            errors.append("failed or blocked criteria must have score 0")
        _validate_references(
            row.get("evidence_observation_ids"),
            observation_ids,
            "trace.criteria_results evidence_observation_ids",
            errors,
        )
        _validate_references(
            row.get("failure_ids"),
            failure_ids,
            "trace.criteria_results failure_ids",
            errors,
        )

    for row in trace["failures"]:
        if not isinstance(row, dict):
            continue
        if row.get("stage") not in FAILURE_STAGES:
            errors.append("trace.failures contains an invalid stage")
        if row.get("type") not in FAILURE_TYPES:
            errors.append("trace.failures contains an invalid type")
        related_action = row.get("related_action_id")
        if related_action is not None and related_action not in action_ids:
            errors.append("trace.failures references an unknown action")
        related_tool_call = row.get("related_tool_call_id")
        if related_tool_call is not None and related_tool_call not in tool_call_ids:
            errors.append("trace.failures references an unknown tool call")
        _validate_references(
            row.get("evidence_observation_ids"),
            observation_ids,
            "trace.failures evidence_observation_ids",
            errors,
        )

    outcome = trace["outcome"]
    if not isinstance(outcome, dict):
        errors.append("trace.outcome must be an object")
    else:
        if outcome.get("status") not in OUTCOME_STATUSES:
            errors.append("trace.outcome.status is invalid")
        criterion_score = outcome.get("criterion_score")
        if not isinstance(criterion_score, (int, float)) or not 0 <= criterion_score <= 1:
            errors.append("trace.outcome.criterion_score must be between 0 and 1")
        if trace["passed"] != (outcome.get("status") == "completed"):
            errors.append("trace.passed must be true only for completed outcomes")
        applicable = [
            row
            for row in trace["criteria_results"]
            if isinstance(row, dict) and row.get("status") != "not_applicable"
        ]
        total_weight = sum(
            float(row.get("weight", 0))
            for row in applicable
            if isinstance(row.get("weight"), (int, float))
        )
        if total_weight > 0 and isinstance(criterion_score, (int, float)):
            derived_score = sum(
                float(row.get("weight", 0)) * float(row.get("score", 0))
                for row in applicable
                if isinstance(row.get("weight"), (int, float))
                and isinstance(row.get("score"), (int, float))
            ) / total_weight
            if round(derived_score, 6) != round(float(criterion_score), 6):
                errors.append(
                    "trace.outcome.criterion_score does not match weighted criteria"
                )
        required_passed = all(
            row.get("status") == "pass"
            for row in trace["criteria_results"]
            if isinstance(row, dict) and row.get("required")
        )
        if outcome.get("required_criteria_passed") != required_passed:
            errors.append(
                "trace.outcome.required_criteria_passed does not match criteria"
            )
        if outcome.get("status") == "completed" and not required_passed:
            errors.append("completed outcomes require all required criteria to pass")

    side_effects = trace["side_effects"]
    if isinstance(side_effects, dict):
        incidents = side_effects.get("incidents")
        incident_count = side_effects.get("incident_count")
        if isinstance(incidents, list) and incident_count != len(incidents):
            errors.append("trace.side_effects incident_count does not match incidents")
    if trace["failure_type"] == "none" and failure_ids:
        errors.append("trace.failure_type cannot be none when failures are recorded")
    if trace["failure_type"] != "none" and not failure_ids:
        errors.append("trace.failure_type requires at least one failure record")

    snapshots = trace["state_snapshots"]
    if not isinstance(snapshots, list) or len(snapshots) < 2:
        errors.append("trace.state_snapshots must contain initial and final snapshots")
    else:
        phases = {
            row.get("phase")
            for row in snapshots
            if isinstance(row, dict)
        }
        if "initial" not in phases or not phases.intersection({"final", "restored"}):
            errors.append("trace.state_snapshots must include initial and final/restored phases")

    verification_rows = trace["verifications"]
    if not isinstance(verification_rows, list):
        errors.append("trace.verifications must be a list")
    else:
        for row in verification_rows:
            if not isinstance(row, dict):
                errors.append("trace.verifications entries must be objects in v0.2")
                continue
            if row.get("criterion_id") not in criterion_ids:
                errors.append("trace.verifications references an unknown criterion")
            _validate_references(
                row.get("evidence_observation_ids"),
                observation_ids,
                "trace.verifications evidence_observation_ids",
                errors,
            )
    return errors


def _validate_id_rows(
    rows: Any,
    *,
    id_field: str,
    label: str,
    errors: list[str],
) -> set[str]:
    if not isinstance(rows, list):
        errors.append(f"{label} must be a list")
        return set()
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append(f"{label} entries must be objects")
            continue
        value = row.get(id_field)
        if not isinstance(value, str) or not value:
            errors.append(f"{label} entries require {id_field}")
        elif value in ids:
            errors.append(f"{label} contains duplicate {id_field}")
        else:
            ids.add(value)
    return ids


def _validate_references(
    values: Any,
    known: set[str],
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(values, list):
        errors.append(f"{label} must be a list")
        return
    if set(values) - known:
        errors.append(f"{label} contains unknown references")
