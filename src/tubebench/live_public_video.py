from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .io import read_json

TASK_SCHEMA_VERSION = "live-public-video-task.v0.1"
TRACE_SCHEMA_VERSION = "live-public-video-trace.v0.1"
TRACK = "live_public_video_v0"

SITES = {"youtube", "mit_ocw", "cspan", "internet_archive", "loc"}
SITE_COUNTS = {
    "youtube": 8,
    "mit_ocw": 5,
    "cspan": 5,
    "internet_archive": 4,
    "loc": 2,
}
SITE_DOMAINS = {
    "youtube": {"www.youtube.com", "youtube.com", "youtu.be"},
    "mit_ocw": {"ocw.mit.edu"},
    "cspan": {"www.c-span.org", "c-span.org"},
    "internet_archive": {"archive.org", "www.archive.org"},
    "loc": {"www.loc.gov", "loc.gov"},
}
VIDEO_TYPES = {
    "lecture",
    "public_affairs",
    "archive_film",
    "public_domain_film",
    "long_music",
    "live_stream",
}
TASK_FAMILIES = {
    "metadata_inspection",
    "transcript_caption_availability",
    "timestamp_localization",
    "visual_evidence",
    "cross_video_comparison",
    "blocked_volatile_reporting",
}
READ_ONLY_ACTIONS = {
    "open_page",
    "observe_page",
    "capture_screenshot",
    "inspect_visible_controls",
    "read_visible_text",
    "record_final_answer",
}
REQUIRED_FORBIDDEN_ACTIONS = {
    "account_login",
    "account_mutation",
    "ad_interaction",
    "comment",
    "download",
    "like",
    "live_chat",
    "purchase",
    "subscribe",
}
VOLATILITY_LEVELS = {"low", "medium", "high"}
MODES = {"gui_native", "ui_assisted", "instrumented_browser"}
OUTCOME_STATUSES = {"completed", "partial", "failed", "blocked", "invalid"}
CRITERION_STATUSES = {"pass", "partial", "fail", "blocked", "not_applicable"}
FAILURE_TYPES = {
    "none",
    "availability_blocked",
    "navigation_failure",
    "video_ui_grounding_failure",
    "media_state_interpretation_failure",
    "transcript_caption_misuse",
    "timestamp_localization_failure",
    "visual_evidence_failure",
    "weak_verification",
    "overconfident_final_answer",
    "runtime_browser_controller_failure",
    "public_site_volatility",
}
FAILURE_STAGES = {
    "availability",
    "navigation",
    "perception",
    "grounding",
    "evidence_collection",
    "verification",
    "final_answer",
    "runtime",
    "evaluation",
}

REQUIRED_TASK_FIELDS = {
    "schema_version",
    "task_id",
    "track",
    "revision",
    "site",
    "url",
    "video_type",
    "task_family",
    "task_prompt",
    "allowed_actions",
    "forbidden_actions",
    "expected_evidence",
    "success_criteria",
    "verification_requirements",
    "volatility_level",
    "candidate_metadata",
}

REQUIRED_TRACE_FIELDS = {
    "schema_version",
    "run_id",
    "attempt_id",
    "task_id",
    "task_revision",
    "track",
    "site",
    "task_family",
    "mode",
    "agent",
    "url",
    "started_at",
    "ended_at",
    "benchmark_git_revision",
    "benchmark_git_dirty",
    "availability",
    "observations",
    "screenshots",
    "page_refs",
    "browser_tool_calls",
    "actions",
    "watched_intervals",
    "criteria_results",
    "final_answer",
    "final_verification",
    "failures",
    "recovery_attempts",
    "side_effects",
    "metrics",
    "outcome",
    "errors",
    "qualitative_notes",
}

SENSITIVE_TRACE_KEYS = {
    "authorization",
    "bearer",
    "browser_history",
    "browser_profile",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "email",
    "full_transcript",
    "local_storage",
    "profile",
    "profile_path",
    "raw_dom",
    "raw_html",
    "session_storage",
    "token",
    "transcript_dump",
}


def default_live_public_video_catalog_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "benchmarks"
        / TRACK
        / "tasks"
        / "catalog.json"
    )


def load_live_public_video_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    value = read_json(path or default_live_public_video_catalog_path())
    if not isinstance(value, list):
        raise ValueError("live public video catalog root must be a JSON array")
    return value


def validate_live_public_video_catalog(tasks: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    site_counts: Counter[str] = Counter()
    families: Counter[str] = Counter()
    for index, task in enumerate(tasks):
        label = task.get("task_id", f"index {index}")
        if not isinstance(task, dict):
            errors.append(f"{label}: task must be an object")
            continue
        missing = sorted(REQUIRED_TASK_FIELDS - set(task))
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
            continue
        unknown = sorted(set(task) - REQUIRED_TASK_FIELDS - {"source_task_id"})
        if unknown:
            errors.append(f"{label}: unknown fields: {', '.join(unknown)}")
        if task["schema_version"] != TASK_SCHEMA_VERSION:
            errors.append(f"{label}: unsupported schema_version")
        if task["track"] != TRACK:
            errors.append(f"{label}: track must be {TRACK}")
        task_id = task["task_id"]
        if not isinstance(task_id, str) or not _looks_like_task_id(task_id):
            errors.append(f"{label}: task_id must match LPV-###")
        elif task_id in seen:
            errors.append(f"{label}: duplicate task id")
        seen.add(str(task_id))
        if not isinstance(task["revision"], int) or isinstance(task["revision"], bool) or task["revision"] < 1:
            errors.append(f"{label}: revision must be a positive integer")
        site = task["site"]
        if site not in SITES:
            errors.append(f"{label}: invalid site")
        else:
            site_counts[str(site)] += 1
        url = task["url"]
        if not _valid_public_url(url, site):
            errors.append(f"{label}: url must be an https public URL for {site}")
        if task["video_type"] not in VIDEO_TYPES:
            errors.append(f"{label}: invalid video_type")
        family = task["task_family"]
        if family not in TASK_FAMILIES:
            errors.append(f"{label}: invalid task_family")
        else:
            families[str(family)] += 1
        if not isinstance(task["task_prompt"], str) or not task["task_prompt"]:
            errors.append(f"{label}: task_prompt must be a non-empty string")
        allowed_actions = task["allowed_actions"]
        if (
            not isinstance(allowed_actions, list)
            or not allowed_actions
            or set(allowed_actions) - READ_ONLY_ACTIONS
            or len(set(allowed_actions)) != len(allowed_actions)
        ):
            errors.append(f"{label}: allowed_actions must be unique read-only actions")
        forbidden_actions = task["forbidden_actions"]
        if not _string_list(forbidden_actions):
            errors.append(f"{label}: forbidden_actions must be unique non-empty strings")
        else:
            missing_forbidden = sorted(REQUIRED_FORBIDDEN_ACTIONS - set(forbidden_actions))
            if missing_forbidden:
                errors.append(
                    f"{label}: forbidden_actions missing required actions: "
                    + ", ".join(missing_forbidden)
                )
            if set(forbidden_actions) & set(allowed_actions):
                errors.append(f"{label}: action cannot be both allowed and forbidden")
        for field in (
            "expected_evidence",
            "success_criteria",
            "verification_requirements",
        ):
            if not _string_list(task[field]):
                errors.append(f"{label}: {field} must be a unique non-empty string list")
        if task["volatility_level"] not in VOLATILITY_LEVELS:
            errors.append(f"{label}: invalid volatility_level")
        metadata = task["candidate_metadata"]
        if not isinstance(metadata, dict):
            errors.append(f"{label}: candidate_metadata must be an object")
        else:
            if not isinstance(metadata.get("verified_at"), str) or not metadata.get("verified_at"):
                errors.append(f"{label}: candidate_metadata.verified_at is required")
            if metadata.get("access") != "public_unauthenticated":
                errors.append(f"{label}: candidate_metadata.access must be public_unauthenticated")
            if not isinstance(metadata.get("source"), str) or not metadata.get("source"):
                errors.append(f"{label}: candidate_metadata.source is required")

    if len(tasks) != sum(SITE_COUNTS.values()):
        errors.append(
            f"live public video catalog must contain {sum(SITE_COUNTS.values())} tasks; "
            f"found {len(tasks)}"
        )
    if dict(site_counts) != SITE_COUNTS:
        errors.append(
            "live public video catalog site counts must be "
            + ", ".join(f"{site}={count}" for site, count in sorted(SITE_COUNTS.items()))
        )
    missing_families = sorted(TASK_FAMILIES - set(families))
    if missing_families:
        errors.append(
            "live public video catalog must cover task families: "
            + ", ".join(missing_families)
        )
    return errors


def validate_live_public_video_trace(trace: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TRACE_FIELDS - set(trace))
    if missing:
        errors.append(f"trace missing fields: {', '.join(missing)}")
        return errors
    sensitive_paths = _find_sensitive_trace_keys(trace)
    if sensitive_paths:
        errors.append(
            "trace contains forbidden raw browser/account fields: "
            + ", ".join(sorted(sensitive_paths))
        )
    if trace["schema_version"] != TRACE_SCHEMA_VERSION:
        errors.append("trace has unsupported schema_version")
    if trace["track"] != TRACK:
        errors.append(f"trace.track must be {TRACK}")
    if not _looks_like_task_id(trace["task_id"]):
        errors.append("trace.task_id must match LPV-###")
    if trace["site"] not in SITES:
        errors.append("trace has invalid site")
    if trace["task_family"] not in TASK_FAMILIES:
        errors.append("trace has invalid task_family")
    if trace["mode"] not in MODES:
        errors.append("trace has invalid mode")
    if not _valid_public_url(trace["url"], trace["site"]):
        errors.append("trace.url must be an https public URL for trace.site")
    if not isinstance(trace["benchmark_git_dirty"], bool):
        errors.append("trace.benchmark_git_dirty must be a boolean")
    availability = trace["availability"]
    if not isinstance(availability, dict) or availability.get("status") not in {
        "available",
        "volatile",
        "blocked",
        "unavailable",
    }:
        errors.append("trace.availability.status is invalid")

    observation_ids = _validate_id_rows(
        trace["observations"],
        id_field="observation_id",
        label="trace.observations",
        errors=errors,
    )
    screenshot_ids = _validate_screenshots(trace["screenshots"], errors)
    page_ref_ids = _validate_page_refs(trace["page_refs"], errors)
    tool_call_ids = _validate_id_rows(
        trace["browser_tool_calls"],
        id_field="tool_call_id",
        label="trace.browser_tool_calls",
        errors=errors,
    )
    action_ids = _validate_id_rows(
        trace["actions"],
        id_field="action_id",
        label="trace.actions",
        errors=errors,
    )
    failure_ids = _validate_id_rows(
        trace["failures"],
        id_field="failure_id",
        label="trace.failures",
        errors=errors,
    )

    if not screenshot_ids:
        errors.append("trace.screenshots must contain at least one private screenshot ref")
    if not observation_ids:
        errors.append("trace.observations must not be empty")
    if not tool_call_ids:
        errors.append("trace.browser_tool_calls must not be empty")

    for row in trace["observations"]:
        if not isinstance(row, dict):
            continue
        confidence = row.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append("trace.observations confidence must be between 0 and 1")
        if not isinstance(row.get("visible_text_snippet"), str):
            errors.append("trace.observations visible_text_snippet must be a string")
        _validate_references(
            row.get("screenshot_refs"),
            screenshot_ids,
            "trace.observations screenshot_refs",
            errors,
            allow_empty=True,
        )
        _validate_references(
            row.get("page_refs"),
            page_ref_ids,
            "trace.observations page_refs",
            errors,
            allow_empty=True,
        )

    for row in trace["actions"]:
        if not isinstance(row, dict):
            continue
        if row.get("action_type") not in READ_ONLY_ACTIONS:
            errors.append("trace.actions contains a non-read-only action_type")

    for row in trace["watched_intervals"]:
        if not isinstance(row, dict):
            errors.append("trace.watched_intervals entries must be objects")
            continue
        start = row.get("start_seconds")
        end = row.get("end_seconds")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end < start:
            errors.append("trace.watched_intervals require ordered numeric start/end")

    criterion_ids = _validate_criteria(
        trace["criteria_results"],
        observation_ids,
        failure_ids,
        errors,
    )
    _validate_failures(trace["failures"], action_ids, tool_call_ids, observation_ids, errors)
    _validate_final_verification(
        trace["final_verification"],
        criterion_ids,
        observation_ids,
        errors,
    )
    _validate_outcome(trace, criterion_ids, errors)
    if not isinstance(trace["final_answer"], dict):
        errors.append("trace.final_answer must be an object")
    if not isinstance(trace["side_effects"], dict):
        errors.append("trace.side_effects must be an object")
    if not isinstance(trace["metrics"], dict):
        errors.append("trace.metrics must be an object")
    if not isinstance(trace["errors"], list):
        errors.append("trace.errors must be a list")
    if not isinstance(trace["qualitative_notes"], dict):
        errors.append("trace.qualitative_notes must be an object")
    return errors


def _looks_like_task_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 7
        and value.startswith("LPV-")
        and value[4:].isdigit()
    )


def _string_list(value: Any, *, non_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not non_empty)
        and all(isinstance(item, str) and item for item in value)
        and len(set(value)) == len(value)
    )


def _valid_public_url(url: Any, site: Any) -> bool:
    if site not in SITE_DOMAINS or not isinstance(url, str):
        return False
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return False
    hostname = parsed.hostname or ""
    if hostname in SITE_DOMAINS[site]:
        return True
    return any(hostname.endswith(f".{domain}") for domain in SITE_DOMAINS[site])


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


def _validate_screenshots(rows: Any, errors: list[str]) -> set[str]:
    ids = _validate_id_rows(
        rows,
        id_field="screenshot_id",
        label="trace.screenshots",
        errors=errors,
    )
    if not isinstance(rows, list):
        return ids
    for row in rows:
        if not isinstance(row, dict):
            continue
        path = row.get("path")
        if not isinstance(path, str) or not path:
            errors.append("trace.screenshots entries require path")
        elif Path(path).is_absolute() or ".." in Path(path).parts:
            errors.append("trace.screenshots path must be a relative artifact path")
        if not isinstance(row.get("description"), str) or not row.get("description"):
            errors.append("trace.screenshots entries require description")
    return ids


def _validate_page_refs(rows: Any, errors: list[str]) -> set[str]:
    ids = _validate_id_rows(
        rows,
        id_field="page_ref_id",
        label="trace.page_refs",
        errors=errors,
    )
    if not isinstance(rows, list):
        return ids
    for row in rows:
        if not isinstance(row, dict):
            continue
        if not isinstance(row.get("url"), str) or not row["url"].startswith("https://"):
            errors.append("trace.page_refs entries require https url")
        if not isinstance(row.get("label"), str) or not row.get("label"):
            errors.append("trace.page_refs entries require label")
    return ids


def _validate_criteria(
    rows: Any,
    observation_ids: set[str],
    failure_ids: set[str],
    errors: list[str],
) -> set[str]:
    criterion_ids = _validate_id_rows(
        rows,
        id_field="criterion_id",
        label="trace.criteria_results",
        errors=errors,
    )
    if not isinstance(rows, list):
        return criterion_ids
    if not rows:
        errors.append("trace.criteria_results must not be empty")
    for row in rows:
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
        weight = row.get("weight")
        if not isinstance(weight, (int, float)) or weight <= 0:
            errors.append("trace.criteria_results weight must be positive")
        if not isinstance(row.get("required"), bool):
            errors.append("trace.criteria_results required must be boolean")
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
            allow_empty=True,
        )
        unsupported = row.get("unsupported_claim_count", 0)
        if not isinstance(unsupported, int) or isinstance(unsupported, bool) or unsupported < 0:
            errors.append("trace.criteria_results unsupported_claim_count must be non-negative")
    return criterion_ids


def _validate_failures(
    rows: Any,
    action_ids: set[str],
    tool_call_ids: set[str],
    observation_ids: set[str],
    errors: list[str],
) -> None:
    if not isinstance(rows, list):
        return
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("type") not in FAILURE_TYPES:
            errors.append("trace.failures contains an invalid type")
        if row.get("stage") not in FAILURE_STAGES:
            errors.append("trace.failures contains an invalid stage")
        if row.get("related_action_id") is not None and row["related_action_id"] not in action_ids:
            errors.append("trace.failures references an unknown action")
        if row.get("related_tool_call_id") is not None and row["related_tool_call_id"] not in tool_call_ids:
            errors.append("trace.failures references an unknown tool call")
        _validate_references(
            row.get("evidence_observation_ids"),
            observation_ids,
            "trace.failures evidence_observation_ids",
            errors,
            allow_empty=True,
        )


def _validate_final_verification(
    value: Any,
    criterion_ids: set[str],
    observation_ids: set[str],
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append("trace.final_verification must be an object")
        return
    rows = value.get("checks")
    if not isinstance(rows, list) or not rows:
        errors.append("trace.final_verification.checks must be a non-empty list")
        return
    for row in rows:
        if not isinstance(row, dict):
            errors.append("trace.final_verification.checks entries must be objects")
            continue
        if row.get("criterion_id") not in criterion_ids:
            errors.append("trace.final_verification references an unknown criterion")
        _validate_references(
            row.get("evidence_observation_ids"),
            observation_ids,
            "trace.final_verification evidence_observation_ids",
            errors,
        )


def _validate_outcome(
    trace: dict[str, Any],
    criterion_ids: set[str],
    errors: list[str],
) -> None:
    outcome = trace["outcome"]
    if not isinstance(outcome, dict):
        errors.append("trace.outcome must be an object")
        return
    if outcome.get("status") not in OUTCOME_STATUSES:
        errors.append("trace.outcome.status is invalid")
    if not isinstance(outcome.get("retained_slot"), bool) or outcome.get("retained_slot") is not True:
        errors.append("trace.outcome.retained_slot must be true")
    criterion_score = outcome.get("criterion_score")
    if not isinstance(criterion_score, (int, float)) or not 0 <= criterion_score <= 1:
        errors.append("trace.outcome.criterion_score must be between 0 and 1")
        return
    criteria = [
        row
        for row in trace["criteria_results"]
        if isinstance(row, dict) and row.get("status") != "not_applicable"
    ]
    total_weight = sum(
        float(row.get("weight", 0))
        for row in criteria
        if isinstance(row.get("weight"), (int, float))
    )
    if total_weight > 0:
        derived = sum(
            float(row.get("weight", 0)) * float(row.get("score", 0))
            for row in criteria
            if isinstance(row.get("weight"), (int, float))
            and isinstance(row.get("score"), (int, float))
        ) / total_weight
        if round(derived, 6) != round(float(criterion_score), 6):
            errors.append("trace.outcome.criterion_score does not match weighted criteria")
    required_passed = all(
        row.get("status") == "pass"
        for row in trace["criteria_results"]
        if isinstance(row, dict) and row.get("required")
    )
    if outcome.get("required_criteria_passed") != required_passed:
        errors.append("trace.outcome.required_criteria_passed does not match criteria")
    if outcome.get("status") == "completed" and not required_passed:
        errors.append("completed outcomes require all required criteria to pass")
    unsupported_total = sum(
        int(row.get("unsupported_claim_count", 0))
        for row in trace["criteria_results"]
        if isinstance(row, dict)
        and isinstance(row.get("unsupported_claim_count", 0), int)
    )
    if outcome.get("unsupported_claim_count") != unsupported_total:
        errors.append("trace.outcome.unsupported_claim_count does not match criteria")
    if not criterion_ids:
        errors.append("trace.outcome requires criteria")


def _validate_references(
    values: Any,
    known: set[str],
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> None:
    if not isinstance(values, list):
        errors.append(f"{label} must be a list")
        return
    if not values and not allow_empty:
        errors.append(f"{label} must not be empty")
    if set(values) - known:
        errors.append(f"{label} contains unknown references")


def _find_sensitive_trace_keys(value: Any, *, prefix: str = "") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            current = f"{prefix}.{key}" if prefix else str(key)
            normalized = str(key).lower().replace("-", "_")
            if normalized in SENSITIVE_TRACE_KEYS:
                paths.add(current)
            paths.update(_find_sensitive_trace_keys(child, prefix=current))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.update(_find_sensitive_trace_keys(child, prefix=f"{prefix}[{index}]"))
    return paths
