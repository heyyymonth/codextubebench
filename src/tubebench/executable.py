from __future__ import annotations

import hashlib
import json
import platform
import random
import subprocess
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from . import __version__
from .io import read_json, write_json
from .state import changed_paths, get_path
from .temporal_metrics import (
    requirement_score,
    temporal_observation_metrics,
    timestamp_localization_error,
    weighted_efficiency,
)

TASK_SCHEMA_VERSION = "tubecontrol-executable-task.v0.1"
TRACE_SCHEMA_VERSION = "tubecontrol-executable-trace.v0.1"
RESULT_SCHEMA_VERSION = "tubecontrol-executable-result.v0.1"
TRACE_SCHEMA_VERSION_V2 = "tubecontrol-executable-trace.v0.2"
RESULT_SCHEMA_VERSION_V2 = "tubecontrol-executable-result.v0.2"
STATIC_RESULT_SCHEMA_VERSION = "codextubebench-static-trace-result.v0.1"
SUITE_ID = "TubeControl-Executable-v0"

REQUIRED_TASK_FIELDS = {
    "schema_version",
    "id",
    "revision",
    "suite",
    "title",
    "instruction",
    "default_mode",
    "supported_modes",
    "initial_state",
    "media",
    "allowed_action_types",
    "allowed_mutations",
    "forbidden_mutations",
    "success",
    "relevant_spans",
    "human_reference",
    "scripted_run",
}

REQUIRED_TRACE_FIELDS = {
    "schema_version",
    "run_id",
    "task_id",
    "task_revision",
    "mode",
    "agent",
    "benchmark_git_revision",
    "benchmark_git_dirty",
    "started_at",
    "ended_at",
    "observations",
    "screenshots",
    "actions",
    "browser_tool_calls",
    "watched_intervals",
    "transcript_cues_used",
    "chapter_ids_used",
    "dom_player_state_reads",
    "verifications",
    "final_answer",
    "final_oracle_state",
    "side_effects",
    "metrics",
    "passed",
    "errors",
}

REQUIRED_TRACE_V2_FIELDS = REQUIRED_TRACE_FIELDS | {
    "state_snapshots",
    "failures",
    "recovery_attempts",
    "final_verification",
    "qualitative_report",
    "step_results",
    "dimensions",
    "outcome",
    "trace_valid",
}

MODES = {
    "gui_native",
    "ui_assisted",
    "instrumented_browser",
    "hybrid",
}

EXECUTABLE_MODE_CHANNELS: dict[str, set[str]] = {
    "gui_native": {
        "screenshot",
        "video_observation",
        "player_state",
    },
    "ui_assisted": {
        "screenshot",
        "video_observation",
        "player_state",
        "transcript",
        "chapters",
        "audit_log",
    },
    "instrumented_browser": {
        "screenshot",
        "video_observation",
        "player_state",
        "transcript",
        "chapters",
        "audit_log",
        "dom_player_state",
    },
    "hybrid": {
        "screenshot",
        "video_observation",
        "player_state",
        "transcript",
        "chapters",
        "audit_log",
        "dom_player_state",
        "local_file",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_executable_catalog_path() -> Path:
    return (
        repository_root()
        / "benchmarks"
        / "tubecontrol_executable_v0"
        / "tasks"
        / "catalog.json"
    )


def load_executable_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    value = read_json(path or default_executable_catalog_path())
    if not isinstance(value, list):
        raise ValueError("executable catalog root must be a JSON array")
    return value


def _valid_span(span: Any, media_ids: set[str]) -> bool:
    return (
        isinstance(span, dict)
        and span.get("media_id") in media_ids
        and isinstance(span.get("start_seconds"), (int, float))
        and isinstance(span.get("end_seconds"), (int, float))
        and span["end_seconds"] > span["start_seconds"] >= 0
    )


def validate_executable_catalog(tasks: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, task in enumerate(tasks):
        label = task.get("id", f"index {index}")
        missing = sorted(REQUIRED_TASK_FIELDS - task.keys())
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
            continue
        if task["schema_version"] != TASK_SCHEMA_VERSION:
            errors.append(f"{label}: unsupported schema_version")
        if task["suite"] != SUITE_ID:
            errors.append(f"{label}: suite must be {SUITE_ID}")
        task_id = task["id"]
        if not isinstance(task_id, str) or not task_id.startswith("TCE-"):
            errors.append(f"{label}: task id must start with TCE-")
        elif task_id in seen:
            errors.append(f"{label}: duplicate task id")
        seen.add(task_id)
        if not isinstance(task["revision"], int) or task["revision"] < 1:
            errors.append(f"{label}: revision must be a positive integer")
        supported_modes = task["supported_modes"]
        if (
            not isinstance(supported_modes, list)
            or not supported_modes
            or set(supported_modes) - MODES
        ):
            errors.append(f"{label}: supported_modes contains an invalid mode")
        if task["default_mode"] not in supported_modes:
            errors.append(f"{label}: default_mode must be supported")
        if not isinstance(task["initial_state"], dict):
            errors.append(f"{label}: initial_state must be an object")
        for field in (
            "media",
            "allowed_action_types",
            "allowed_mutations",
            "forbidden_mutations",
            "relevant_spans",
        ):
            if not isinstance(task[field], list):
                errors.append(f"{label}: {field} must be a list")
        media_ids = {
            row.get("media_id")
            for row in task["media"]
            if isinstance(row, dict)
        }
        if not media_ids or None in media_ids or len(media_ids) != len(task["media"]):
            errors.append(f"{label}: media ids must be present and unique")
        for row in task["media"]:
            if not isinstance(row.get("duration_seconds"), (int, float)) or row[
                "duration_seconds"
            ] <= 0:
                errors.append(f"{label}: media duration must be positive")
            for cue in row.get("transcript", []):
                if not _valid_span(cue, {row.get("media_id")}):
                    errors.append(f"{label}: invalid transcript cue")
            for chapter in row.get("chapters", []):
                if not isinstance(chapter, dict) or not isinstance(
                    chapter.get("start_seconds"), (int, float)
                ):
                    errors.append(f"{label}: invalid chapter")
        for span in task["relevant_spans"]:
            if not _valid_span(span, media_ids):
                errors.append(f"{label}: invalid relevant span")
        success = task["success"]
        if not isinstance(success, dict):
            errors.append(f"{label}: success must be an object")
        else:
            for predicate in success.get("state_predicates", []):
                if set(predicate) != {"path", "equals"}:
                    errors.append(f"{label}: state predicates require path and equals")
            answer = success.get("answer")
            if answer is not None and answer.get("type") not in {
                "exact",
                "contains_all",
                "timestamp",
            }:
                errors.append(f"{label}: unsupported answer evaluator")
        reference = task["human_reference"]
        for field in ("steps", "watched_seconds"):
            if not isinstance(reference.get(field), (int, float)) or reference[
                field
            ] < 0:
                errors.append(f"{label}: human_reference.{field} must be non-negative")
        scripted = task["scripted_run"]
        if not isinstance(scripted, dict) or not isinstance(
            scripted.get("actions"), list
        ):
            errors.append(f"{label}: scripted_run.actions must be a list")
    if len(tasks) != 12:
        errors.append(f"{SUITE_ID} must contain exactly 12 tasks; found {len(tasks)}")
    return errors


def validate_executable_trace(trace: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    schema_version = trace.get("schema_version")
    required_fields = (
        REQUIRED_TRACE_V2_FIELDS
        if schema_version == TRACE_SCHEMA_VERSION_V2
        else REQUIRED_TRACE_FIELDS
    )
    missing = sorted(required_fields - trace.keys())
    if missing:
        errors.append(f"trace missing fields: {', '.join(missing)}")
    if schema_version not in {TRACE_SCHEMA_VERSION, TRACE_SCHEMA_VERSION_V2}:
        errors.append("trace has unsupported schema_version")
    if trace.get("mode") not in MODES:
        errors.append("trace has invalid mode")
    for field in (
        "observations",
        "screenshots",
        "actions",
        "browser_tool_calls",
        "watched_intervals",
        "transcript_cues_used",
        "chapter_ids_used",
        "dom_player_state_reads",
        "verifications",
        "errors",
    ):
        if not isinstance(trace.get(field), list):
            errors.append(f"trace.{field} must be a list")
    if schema_version == TRACE_SCHEMA_VERSION_V2:
        for field in (
            "state_snapshots",
            "failures",
            "recovery_attempts",
            "step_results",
        ):
            if not isinstance(trace.get(field), list):
                errors.append(f"trace.{field} must be a list")
        for field in ("final_verification", "qualitative_report", "dimensions", "outcome"):
            if not isinstance(trace.get(field), dict):
                errors.append(f"trace.{field} must be an object")
        if not isinstance(trace.get("trace_valid"), bool):
            errors.append("trace.trace_valid must be boolean")
        id_specs = (
            ("observations", "observation_id"),
            ("actions", "action_id"),
            ("browser_tool_calls", "tool_call_id"),
            ("state_snapshots", "snapshot_id"),
            ("failures", "failure_id"),
            ("recovery_attempts", "recovery_id"),
        )
        for field, id_field in id_specs:
            rows = trace.get(field, [])
            if not isinstance(rows, list):
                continue
            values = [row.get(id_field) for row in rows if isinstance(row, dict)]
            if len(values) != len(rows) or any(
                not isinstance(value, str) or not value for value in values
            ):
                errors.append(f"trace.{field} entries require {id_field}")
            elif len(values) != len(set(values)):
                errors.append(f"trace.{field} contains duplicate {id_field}")
        outcome = trace.get("outcome")
        if isinstance(outcome, dict) and outcome.get("status") not in {
            "completed",
            "partial",
            "failed",
            "blocked",
            "invalid",
        }:
            errors.append("trace.outcome.status is invalid")
    if not isinstance(trace.get("metrics"), dict):
        errors.append("trace.metrics must be an object")
    if not isinstance(trace.get("side_effects"), dict):
        errors.append("trace.side_effects must be an object")
    execution_surface = trace.get("execution_surface")
    if execution_surface is not None and not isinstance(execution_surface, dict):
        errors.append("trace.execution_surface must be an object when present")
    elif isinstance(execution_surface, dict):
        required_surface_fields = {
            "type",
            "public_url",
            "fixture_version",
            "deployment_id",
        }
        if set(execution_surface) != required_surface_fields:
            errors.append(
                "trace.execution_surface must contain only type, public_url, "
                "fixture_version, and deployment_id"
            )
        if execution_surface.get("type") not in {
            "local",
            "hosted_https",
            "provider_runner",
            "manual",
        }:
            errors.append("trace.execution_surface.type is invalid")
        for field in ("public_url", "fixture_version", "deployment_id"):
            if (
                not isinstance(execution_surface.get(field), str)
                or not execution_surface[field]
            ):
                errors.append(
                    f"trace.execution_surface.{field} must be a non-empty string"
                )
    return errors


def benchmark_provenance() -> tuple[str, bool | None]:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root(),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "uncommitted", None
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repository_root(),
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    return revision, dirty


def catalog_digest(tasks: list[dict[str, Any]]) -> str:
    payload = json.dumps(tasks, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _path_allowed(path: str, allowed: list[str]) -> bool:
    return any(path == item or path.startswith(f"{item}.") for item in allowed)


def _current_chapter(media: dict[str, Any], current_time: float) -> str | None:
    current: str | None = None
    for chapter in media.get("chapters", []):
        if float(chapter["start_seconds"]) <= current_time:
            current = str(chapter["id"])
    return current


def agent_view(task: dict[str, Any], state: dict[str, Any], mode: str) -> dict[str, Any]:
    media_by_id = {row["media_id"]: row for row in task["media"]}
    players: dict[str, Any] = {}
    for player_id, player in state.get("players", {}).items():
        media = media_by_id[player["media_id"]]
        players[player_id] = {
            "media_id": player["media_id"],
            "title": media["title"],
            "playback": player["playback"],
            "current_time": player["current_time"],
            "duration": player["duration"],
            "muted": player["muted"],
            "playback_rate": player["playback_rate"],
            "chapter_id": _current_chapter(media, float(player["current_time"])),
            "visual_event": next(
                (
                    event["label"]
                    for event in media.get("visual_events", [])
                    if event["start_seconds"]
                    <= float(player["current_time"])
                    <= event["end_seconds"]
                ),
                None,
            ),
        }
    view: dict[str, Any] = {
        "task": {
            "id": task["id"],
            "title": task["title"],
            "instruction": task["instruction"],
            "mode": mode,
            "allowed_action_types": task["allowed_action_types"],
            "verification_requirements": task["success"].get(
                "verification_requirements", []
            ),
        },
        "players": players,
        "audit_log": deepcopy(state.get("audit_log", [])),
    }
    if mode in {"ui_assisted", "instrumented_browser", "hybrid"}:
        view["transcripts"] = {
            row["media_id"]: deepcopy(row.get("transcript", []))
            for row in task["media"]
        }
        view["chapters"] = {
            row["media_id"]: deepcopy(row.get("chapters", []))
            for row in task["media"]
        }
    if mode in {"instrumented_browser", "hybrid"}:
        view["instrumented_player_state"] = deepcopy(players)
    return view


def _apply_action(
    task: dict[str, Any],
    state: dict[str, Any],
    action: dict[str, Any],
    mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    action_type = action.get("type")
    if action_type not in task["allowed_action_types"]:
        raise ValueError(f"action type is not allowed for {task['id']}: {action_type}")
    watched: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    transcript_cues: list[str] = []
    chapter_ids: list[str] = []
    player_id = action.get("player_id")
    player = state.get("players", {}).get(player_id) if player_id else None
    if action_type in {"play", "pause", "seek", "set_muted", "set_rate", "watch"}:
        if player is None:
            raise ValueError(f"unknown player: {player_id}")
    if action_type == "play":
        player["playback"] = "playing"
    elif action_type == "pause":
        player["playback"] = "paused"
    elif action_type == "seek":
        target = float(action["seconds"])
        player["current_time"] = min(max(target, 0.0), float(player["duration"]))
    elif action_type == "set_muted":
        player["muted"] = bool(action["value"])
    elif action_type == "set_rate":
        player["playback_rate"] = float(action["value"])
    elif action_type == "watch":
        start = float(player["current_time"])
        seconds = max(0.0, float(action["seconds"]))
        end = min(start + seconds, float(player["duration"]))
        player["current_time"] = end
        watched.append(
            {
                "media_id": player["media_id"],
                "start_seconds": start,
                "end_seconds": end,
                "attention": True,
            }
        )
        observations.append(
            {
                "channel": "video_observation",
                "media_id": player["media_id"],
                "details": {"start_seconds": start, "end_seconds": end},
            }
        )
    elif action_type == "observe":
        channel = str(action["channel"])
        if channel not in EXECUTABLE_MODE_CHANNELS[mode]:
            raise ValueError(f"{mode} does not permit channel: {channel}")
        observations.append(
            {
                "channel": channel,
                "media_id": action.get("media_id"),
                "details": deepcopy(action.get("details", {})),
            }
        )
        if action.get("cue_id"):
            transcript_cues.append(str(action["cue_id"]))
        if action.get("chapter_id"):
            chapter_ids.append(str(action["chapter_id"]))
    elif action_type == "verify":
        channel = str(action.get("channel", "player_state"))
        if channel not in EXECUTABLE_MODE_CHANNELS[mode]:
            raise ValueError(f"{mode} does not permit channel: {channel}")
        observations.append(
            {
                "channel": channel,
                "details": {"verification": action.get("name")},
            }
        )
    return watched, observations, transcript_cues, chapter_ids


def parse_timestamp(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.strip()
    try:
        return float(text)
    except ValueError:
        pass
    parts = text.split(":")
    if len(parts) not in {2, 3}:
        return None
    try:
        numbers = [float(part) for part in parts]
    except ValueError:
        return None
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]


def _answer_result(answer_spec: dict[str, Any] | None, answer: Any) -> tuple[bool, float | None]:
    if answer_spec is None:
        return True, None
    kind = answer_spec["type"]
    if kind == "exact":
        expected = answer_spec["value"]
        if isinstance(expected, str) and isinstance(answer, str):
            return expected.strip().casefold() == answer.strip().casefold(), None
        return expected == answer, None
    if kind == "contains_all":
        text = str(answer).casefold()
        return all(str(item).casefold() in text for item in answer_spec["values"]), None
    predicted = parse_timestamp(answer)
    if predicted is None:
        return False, None
    error = timestamp_localization_error(predicted, answer_spec["target_spans"])
    return bool(error is not None and error <= answer_spec["tolerance_seconds"]), error


def evaluate_executable_trace(
    task: dict[str, Any],
    trace: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if trace.get("schema_version") == TRACE_SCHEMA_VERSION_V2:
        return _evaluate_executable_trace_v2(task, trace)
    state = deepcopy(task["initial_state"])
    incidents: list[dict[str, Any]] = []
    watched_intervals: list[dict[str, Any]] = []
    replay_errors: list[str] = []
    for sequence, observation in enumerate(trace.get("observations", []), 1):
        channel = observation.get("channel")
        if channel and channel not in EXECUTABLE_MODE_CHANNELS[trace["mode"]]:
            replay_errors.append(
                f"observation {sequence}: {trace['mode']} does not permit channel: {channel}"
            )
    for sequence, action in enumerate(trace.get("actions", []), 1):
        before = deepcopy(state)
        try:
            watched, _, _, _ = _apply_action(task, state, action, trace["mode"])
            watched_intervals.extend(watched)
        except (KeyError, TypeError, ValueError) as error:
            replay_errors.append(f"action {sequence}: {error}")
            continue
        for path in sorted(changed_paths(before, state)):
            forbidden = _path_allowed(path, task["forbidden_mutations"])
            allowed = _path_allowed(path, task["allowed_mutations"])
            if forbidden or not allowed:
                incidents.append(
                    {
                        "sequence": sequence,
                        "path": path,
                        "before": get_path(before, path),
                        "after": get_path(state, path),
                        "restored_in_final_state": get_path(
                            task["initial_state"], path
                        )
                        == get_path(state, path),
                        "severity": "critical" if forbidden else "major",
                    }
                )

    predicate_results: list[dict[str, Any]] = []
    for predicate in task["success"].get("state_predicates", []):
        actual = get_path(state, predicate["path"])
        predicate_results.append(
            {
                "path": predicate["path"],
                "expected": predicate["equals"],
                "actual": actual,
                "passed": actual == predicate["equals"],
            }
        )
    answer_passed, timestamp_error = _answer_result(
        task["success"].get("answer"),
        trace.get("final_answer"),
    )
    exact_success = answer_passed and all(
        row["passed"] for row in predicate_results
    ) and not replay_errors

    observation_channels = {
        str(row.get("channel"))
        for row in trace.get("observations", [])
        if row.get("channel")
    }
    accepted_channels = set(task["success"].get("accepted_evidence_channels", []))
    evidence_passed = not accepted_channels or bool(
        observation_channels & accepted_channels
    )
    grounded_success = exact_success and evidence_passed
    disturbance_free = not incidents
    passed = grounded_success and disturbance_free

    media_durations = {
        row["media_id"]: float(row["duration_seconds"]) for row in task["media"]
    }
    temporal = temporal_observation_metrics(
        media_durations,
        watched_intervals,
        task["relevant_spans"],
    )
    verification_requirements = task["success"].get(
        "verification_requirements", []
    )
    verification_score = requirement_score(
        verification_requirements,
        trace.get("verifications", []),
    )
    restoration_required = any(
        "restor" in str(requirement).casefold()
        or "original_state" in str(requirement).casefold()
        for requirement in verification_requirements
    )
    state_restoration_score = (
        round(
            sum(bool(row["passed"]) for row in predicate_results)
            / len(predicate_results),
            6,
        )
        if restoration_required and predicate_results
        else None
    )
    actual_resources = {
        "steps": float(len(trace.get("actions", []))),
        "watched_seconds": float(temporal["watched_seconds"]),
    }
    reference = {
        "steps": float(task["human_reference"]["steps"]),
        "watched_seconds": float(task["human_reference"]["watched_seconds"]),
    }
    efficiency = weighted_efficiency(
        success=passed,
        actual=actual_resources,
        reference=reference,
        weights={"steps": 0.6, "watched_seconds": 0.4},
    )
    side_effects = {
        "disturbance_free": disturbance_free,
        "critical": any(row["severity"] == "critical" for row in incidents),
        "incident_count": len(incidents),
        "severity_points": sum(
            3 if row["severity"] == "critical" else 1 for row in incidents
        ),
        "incidents": incidents,
    }
    metrics = {
        "success": exact_success,
        "grounded_success": grounded_success,
        "disturbance_free_success": passed,
        "step_count": len(trace.get("actions", [])),
        "browser_tool_call_count": len(trace.get("browser_tool_calls", [])),
        "verification_score": verification_score,
        "side_effect_incident_count": len(incidents),
        "state_restoration_score": state_restoration_score,
        "timestamp_localization_error_seconds": timestamp_error,
        "watch_time_seconds": temporal["watched_seconds"],
        "watch_ratio": temporal["watch_ratio"],
        "failure_category": None,
        "relevant_watch_ratio": temporal["relevant_watch_ratio"],
        "over_observation_score": temporal["over_observation_score"],
        "under_observation_score": temporal["under_observation_score"],
        "weighted_efficiency": efficiency,
        "state_tracking_score": None,
        "information_channel_selection": (
            1.0 if evidence_passed and accepted_channels else None
        ),
        "cost": deepcopy(
            trace.get(
                "cost",
                {
                    "model_calls": None,
                    "input_tokens": None,
                    "output_tokens": None,
                    "usd": None,
                },
            )
        ),
        "latency": deepcopy(
            trace.get(
                "latency",
                {
                    "wall_clock_seconds": None,
                    "active_agent_seconds": None,
                    "playback_wall_seconds": temporal["watched_seconds"],
                },
            )
        ),
        "metric_status": {
            "implemented": [
                "success",
                "step_count",
                "browser_tool_call_count",
                "side_effects",
                "side_effect_incident_count",
                "verification_score",
                "timestamp_localization_error_seconds",
                "watch_time_seconds",
                "watch_ratio",
                "weighted_efficiency",
            ],
            "partial": [
                "state_restoration_score",
                "relevant_watch_ratio",
                "over_observation_score",
                "under_observation_score",
                "information_channel_selection",
                "cost",
                "latency",
            ],
            "future": ["failure_category", "state_tracking_score"],
        },
        "predicate_results": predicate_results,
    }
    evaluated = deepcopy(trace)
    evaluated["watched_intervals"] = watched_intervals
    evaluated["final_oracle_state"] = state
    evaluated["side_effects"] = side_effects
    evaluated["metrics"] = metrics
    evaluated["passed"] = passed
    evaluated["errors"] = list(trace.get("errors", [])) + replay_errors
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": trace["run_id"],
        "task_id": task["id"],
        "task_revision": task["revision"],
        "mode": trace["mode"],
        "agent": trace["agent"],
        "benchmark_git_revision": trace["benchmark_git_revision"],
        "benchmark_git_dirty": trace["benchmark_git_dirty"],
        "passed": passed,
        "metrics": metrics,
        "side_effects": side_effects,
        "errors": evaluated["errors"],
    }
    return evaluated, result


def _fraction(passed: int, applicable: int) -> float | None:
    return round(passed / applicable, 6) if applicable else None


def _answer_atoms(
    answer_spec: dict[str, Any] | None,
    answer: Any,
) -> tuple[list[dict[str, Any]], float | None]:
    if answer_spec is None:
        return [], None
    kind = answer_spec["type"]
    if kind == "contains_all":
        text = str(answer).casefold()
        return (
            [
                {
                    "criterion_id": f"answer-contains-{index}",
                    "expected": value,
                    "passed": str(value).casefold() in text,
                }
                for index, value in enumerate(answer_spec["values"], 1)
            ],
            None,
        )
    passed, timestamp_error = _answer_result(answer_spec, answer)
    expected: Any = answer_spec.get("value")
    if kind == "timestamp":
        expected = {
            "target_spans": deepcopy(answer_spec["target_spans"]),
            "tolerance_seconds": answer_spec["tolerance_seconds"],
        }
    return (
        [
            {
                "criterion_id": f"answer-{kind}",
                "expected": expected,
                "actual": answer,
                "passed": passed,
            }
        ],
        timestamp_error,
    )


def _action_matches_reference(task: dict[str, Any], action: dict[str, Any]) -> bool:
    ignored = {"action_id", "timestamp"}
    for reference in task["scripted_run"].get("actions", []):
        if all(action.get(key) == value for key, value in reference.items() if key not in ignored):
            return True
    return False


def _evaluate_executable_trace_v2(
    task: dict[str, Any],
    trace: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    state = deepcopy(task["initial_state"])
    initial_state = deepcopy(task["initial_state"])
    incidents: list[dict[str, Any]] = []
    watched_intervals: list[dict[str, Any]] = []
    replay_errors: list[str] = []
    step_results: list[dict[str, Any]] = []
    recovery_attempts: list[dict[str, Any]] = []
    pending_failure_ids: list[str] = []

    accepted_channels = set(task["success"].get("accepted_evidence_channels", []))
    verification_requirements = task["success"].get("verification_requirements", [])
    predicates = task["success"].get("state_predicates", [])
    observations_by_sequence: dict[int, list[dict[str, Any]]] = {}
    observation_by_id: dict[str, dict[str, Any]] = {}
    for observation in trace.get("observations", []):
        if not isinstance(observation, dict):
            continue
        sequence = observation.get("sequence")
        if isinstance(sequence, int):
            observations_by_sequence.setdefault(sequence, []).append(observation)
        observation_id = observation.get("observation_id")
        if isinstance(observation_id, str):
            observation_by_id[observation_id] = observation
        channel = observation.get("channel")
        if channel and channel not in EXECUTABLE_MODE_CHANNELS[trace["mode"]]:
            replay_errors.append(
                f"observation {observation_id or '?'}: {trace['mode']} does not permit channel: {channel}"
            )

    trace_failures = [
        row for row in trace.get("failures", []) if isinstance(row, dict)
    ]
    failure_ids_by_action: dict[str, list[str]] = {}
    for failure in trace_failures:
        action_id = failure.get("related_action_id")
        failure_id = failure.get("failure_id")
        if isinstance(action_id, str) and isinstance(failure_id, str):
            failure_ids_by_action.setdefault(action_id, []).append(failure_id)

    for sequence, action in enumerate(trace.get("actions", []), 1):
        before = deepcopy(state)
        before_predicates = {
            predicate["path"]: get_path(before, predicate["path"]) == predicate["equals"]
            for predicate in predicates
        }
        action_id = str(action.get("action_id") or f"action-{sequence:04d}")
        valid = True
        error_text: str | None = None
        try:
            watched, _, _, _ = _apply_action(task, state, action, trace["mode"])
            watched_intervals.extend(watched)
        except (KeyError, TypeError, ValueError) as error:
            valid = False
            error_text = str(error)
            replay_errors.append(f"action {sequence}: {error}")
            state = before

        changed = sorted(changed_paths(before, state)) if valid else []
        step_incidents: list[dict[str, Any]] = []
        for path in changed:
            forbidden = _path_allowed(path, task["forbidden_mutations"])
            allowed = _path_allowed(path, task["allowed_mutations"])
            if forbidden or not allowed:
                incident = {
                    "sequence": sequence,
                    "action_id": action_id,
                    "path": path,
                    "before": get_path(before, path),
                    "after": get_path(state, path),
                    "restored_in_final_state": False,
                    "severity": "critical" if forbidden else "major",
                }
                incidents.append(incident)
                step_incidents.append(incident)

        progress_paths = [
            predicate["path"]
            for predicate in predicates
            if not before_predicates[predicate["path"]]
            and get_path(state, predicate["path"]) == predicate["equals"]
        ]
        restoration_paths = [
            path
            for path in changed
            if get_path(before, path) != get_path(initial_state, path)
            and get_path(state, path) == get_path(initial_state, path)
        ]
        step_observations = observations_by_sequence.get(sequence, [])
        evidence_ids = [
            str(row["observation_id"])
            for row in step_observations
            if row.get("channel") in accepted_channels and row.get("observation_id")
        ]
        evidence_action = action.get("type") in {"observe", "verify", "watch"}
        evidence_collected = evidence_action and bool(evidence_ids)
        verification_completed = (
            action.get("type") == "verify"
            and action.get("name") in verification_requirements
        )
        reference_aligned = valid and _action_matches_reference(task, action)
        related_failure_ids = failure_ids_by_action.get(action_id, [])
        if not valid and not related_failure_ids:
            related_failure_ids = [f"failure-replay-{sequence:04d}"]
        if related_failure_ids:
            pending_failure_ids.extend(related_failure_ids)
        recovered = bool(
            valid
            and pending_failure_ids
            and (
                progress_paths
                or restoration_paths
                or evidence_collected
                or verification_completed
                or reference_aligned
            )
        )
        if recovered:
            recovery_id = f"recovery-{len(recovery_attempts) + 1:04d}"
            recovery_attempts.append(
                {
                    "recovery_id": recovery_id,
                    "failure_ids": list(dict.fromkeys(pending_failure_ids)),
                    "related_action_id": action_id,
                    "succeeded": True,
                }
            )
            pending_failure_ids.clear()
        disturbing = bool(step_incidents)
        useful = bool(
            valid
            and not disturbing
            and (
                progress_paths
                or restoration_paths
                or evidence_collected
                or verification_completed
                or reference_aligned
                or recovered
            )
        )
        step_results.append(
            {
                "action_id": action_id,
                "sequence": sequence,
                "action_type": action.get("type"),
                "valid": valid,
                "permitted": valid and not disturbing,
                "reference_aligned": reference_aligned,
                "progress_paths": progress_paths,
                "changed_paths": changed,
                "restoration_paths": restoration_paths,
                "evidence_observation_ids": evidence_ids,
                "evidence_collected": evidence_collected,
                "verification_completed": verification_completed,
                "recovery_succeeded": recovered,
                "disturbing": disturbing,
                "useful": useful,
                "redundant": valid and not disturbing and not useful,
                "error": error_text,
            }
        )

    for incident in incidents:
        incident["restored_in_final_state"] = get_path(
            initial_state, incident["path"]
        ) == get_path(state, incident["path"])

    predicate_results: list[dict[str, Any]] = []
    initial_predicate_results: list[dict[str, Any]] = []
    for index, predicate in enumerate(predicates, 1):
        initial_value = get_path(initial_state, predicate["path"])
        actual = get_path(state, predicate["path"])
        initial_predicate_results.append(
            {
                "criterion_id": f"state-{index:02d}",
                "path": predicate["path"],
                "passed": initial_value == predicate["equals"],
            }
        )
        predicate_results.append(
            {
                "criterion_id": f"state-{index:02d}",
                "path": predicate["path"],
                "expected": predicate["equals"],
                "actual": actual,
                "passed": actual == predicate["equals"],
            }
        )
    answer_results, timestamp_error = _answer_atoms(
        task["success"].get("answer"), trace.get("final_answer")
    )
    state_passed = sum(bool(row["passed"]) for row in predicate_results)
    answer_passed_count = sum(bool(row["passed"]) for row in answer_results)
    correctness_applicable = len(predicate_results) + len(answer_results)
    correctness_passed = state_passed + answer_passed_count
    correctness_complete = correctness_passed == correctness_applicable

    accepted_observation_ids = [
        str(row["observation_id"])
        for row in trace.get("observations", [])
        if isinstance(row, dict)
        and row.get("channel") in accepted_channels
        and row.get("observation_id")
    ]
    attributable_evidence_observation_ids = [
        str(row["observation_id"])
        for row in trace.get("observations", [])
        if isinstance(row, dict)
        and isinstance(row.get("sequence"), int)
        and row["sequence"] > 0
        and row.get("channel") in accepted_channels
        and row.get("observation_id")
    ]
    evidence_passed = not accepted_channels or bool(accepted_observation_ids)
    evidence_applicable = max(correctness_applicable, 1) if accepted_channels else 0
    evidence_covered = evidence_applicable if evidence_passed else 0

    verification_check_by_name: dict[str, dict[str, Any]] = {}
    final_verification = trace.get("final_verification", {})
    if isinstance(final_verification, dict):
        for check in final_verification.get("checks", []):
            if isinstance(check, dict) and isinstance(check.get("requirement"), str):
                verification_check_by_name[check["requirement"]] = check
    verification_results: list[dict[str, Any]] = []
    for requirement in verification_requirements:
        check = verification_check_by_name.get(requirement, {})
        evidence_refs = [
            value
            for value in check.get("evidence_observation_ids", [])
            if value in observation_by_id
            and observation_by_id[value].get("channel") in accepted_channels
        ]
        performed = requirement in trace.get("verifications", [])
        verification_results.append(
            {
                "requirement": requirement,
                "performed": performed,
                "evidence_observation_ids": evidence_refs,
                "passed": performed and bool(evidence_refs),
            }
        )
    verification_passed_count = sum(
        bool(row["passed"]) for row in verification_results
    )
    verification_complete = verification_passed_count == len(verification_results)

    media_durations = {
        row["media_id"]: float(row["duration_seconds"]) for row in task["media"]
    }
    temporal = temporal_observation_metrics(
        media_durations, watched_intervals, task["relevant_spans"]
    )
    valid_steps = sum(bool(row["valid"]) for row in step_results)
    useful_steps = sum(bool(row["useful"]) for row in step_results)
    redundant_steps = sum(bool(row["redundant"]) for row in step_results)
    disturbing_steps = sum(bool(row["disturbing"]) for row in step_results)
    invalid_steps = len(step_results) - valid_steps
    reference_steps = float(task["human_reference"]["steps"])
    reference_watch = float(task["human_reference"]["watched_seconds"])
    restoration_required = any(
        "restor" in str(requirement).casefold()
        or "original_state" in str(requirement).casefold()
        for requirement in verification_requirements
    )
    restoration_passed = state_passed if restoration_required else 0
    restoration_applicable = len(predicate_results) if restoration_required else 0
    disturbance_free = not incidents
    critical_incident = any(row["severity"] == "critical" for row in incidents)
    trace_valid = not replay_errors
    exact_success = correctness_complete and trace_valid
    grounded_success = exact_success and evidence_passed
    disturbance_free_success = grounded_success and disturbance_free
    completed = (
        grounded_success
        and verification_complete
        and disturbance_free
        and trace_valid
    )
    newly_satisfied = sum(
        1
        for initial, final in zip(initial_predicate_results, predicate_results)
        if not initial["passed"] and final["passed"]
    )
    task_positive = bool(
        newly_satisfied
        or answer_passed_count
        or attributable_evidence_observation_ids
        or verification_passed_count
        or any(row["restoration_paths"] for row in step_results)
    )
    if not trace_valid:
        outcome_status = "invalid"
    elif completed:
        outcome_status = "completed"
    elif critical_incident or not task_positive:
        outcome_status = "failed"
    else:
        outcome_status = "partial"

    side_effects = {
        "disturbance_free": disturbance_free,
        "critical": critical_incident,
        "incident_count": len(incidents),
        "severity_points": sum(
            3 if row["severity"] == "critical" else 1 for row in incidents
        ),
        "transient_incident_count": sum(
            bool(row["restored_in_final_state"]) for row in incidents
        ),
        "final_incident_count": sum(
            not bool(row["restored_in_final_state"]) for row in incidents
        ),
        "incidents": incidents,
    }
    dimensions = {
        "state_correctness": {
            "passed": state_passed,
            "applicable": len(predicate_results),
            "rate": _fraction(state_passed, len(predicate_results)),
            "criteria": predicate_results,
        },
        "answer_correctness": {
            "passed": answer_passed_count,
            "applicable": len(answer_results),
            "rate": _fraction(answer_passed_count, len(answer_results)),
            "criteria": answer_results,
            "timestamp_error_seconds": timestamp_error,
        },
        "evidence_grounding": {
            "passed": evidence_covered,
            "applicable": evidence_applicable,
            "rate": _fraction(evidence_covered, evidence_applicable),
            "accepted_observation_ids": accepted_observation_ids,
        },
        "verification": {
            "passed": verification_passed_count,
            "applicable": len(verification_results),
            "rate": _fraction(verification_passed_count, len(verification_results)),
            "criteria": verification_results,
        },
        "protected_state": {
            "incident_free": disturbance_free,
            "incident_count": len(incidents),
            "critical_incident_count": sum(
                row["severity"] == "critical" for row in incidents
            ),
            "transient_incident_count": side_effects["transient_incident_count"],
            "final_incident_count": side_effects["final_incident_count"],
        },
        "restoration": {
            "passed": restoration_passed,
            "applicable": restoration_applicable,
            "rate": _fraction(restoration_passed, restoration_applicable),
        },
        "step_execution": {
            "total": len(step_results),
            "valid": valid_steps,
            "useful": useful_steps,
            "redundant": redundant_steps,
            "invalid": invalid_steps,
            "disturbing": disturbing_steps,
            "valid_rate": _fraction(valid_steps, len(step_results)),
            "useful_rate": _fraction(useful_steps, len(step_results)),
            "redundant_rate": _fraction(redundant_steps, len(step_results)),
            "invalid_rate": _fraction(invalid_steps, len(step_results)),
            "disturbing_rate": _fraction(disturbing_steps, len(step_results)),
        },
        "recovery": {
            "attempted": len(recovery_attempts),
            "succeeded": sum(bool(row["succeeded"]) for row in recovery_attempts),
            "success_rate": _fraction(
                sum(bool(row["succeeded"]) for row in recovery_attempts),
                len(recovery_attempts),
            ),
        },
        "temporal": {
            "watched_seconds": temporal["watched_seconds"],
            "watch_ratio": temporal["watch_ratio"],
            "relevant_watch_ratio": temporal["relevant_watch_ratio"],
            "over_observation_score": temporal["over_observation_score"],
            "under_observation_score": temporal["under_observation_score"],
            "timestamp_error_seconds": timestamp_error,
        },
        "efficiency": {
            "action_count": len(step_results),
            "reference_action_count": reference_steps,
            "action_reference_ratio": (
                round(len(step_results) / reference_steps, 6)
                if reference_steps
                else None
            ),
            "watched_seconds": temporal["watched_seconds"],
            "reference_watched_seconds": reference_watch,
            "watch_reference_ratio": (
                round(float(temporal["watched_seconds"]) / reference_watch, 6)
                if reference_watch
                else None
            ),
        },
        "trace": {
            "valid": trace_valid,
            "error_count": len(replay_errors),
            "failure_stage": (
                trace_failures[0].get("stage")
                if trace_failures
                else ("action" if replay_errors else None)
            ),
        },
    }
    metrics = {
        "success": exact_success,
        "grounded_success": grounded_success,
        "disturbance_free_success": disturbance_free_success,
        "step_count": len(step_results),
        "browser_tool_call_count": len(trace.get("browser_tool_calls", [])),
        "verification_score": _fraction(
            verification_passed_count, len(verification_results)
        ),
        "side_effect_incident_count": len(incidents),
        "state_restoration_score": _fraction(
            restoration_passed, restoration_applicable
        ),
        "timestamp_localization_error_seconds": timestamp_error,
        "watch_time_seconds": temporal["watched_seconds"],
        "watch_ratio": temporal["watch_ratio"],
        "failure_category": (
            trace_failures[0].get("type") if trace_failures else None
        ),
        "relevant_watch_ratio": temporal["relevant_watch_ratio"],
        "over_observation_score": temporal["over_observation_score"],
        "under_observation_score": temporal["under_observation_score"],
        "state_tracking_score": None,
        "information_channel_selection": 1.0 if evidence_passed and accepted_channels else None,
        "cost": deepcopy(
            trace.get(
                "cost",
                {"model_calls": None, "input_tokens": None, "output_tokens": None, "usd": None},
            )
        ),
        "latency": deepcopy(
            trace.get(
                "latency",
                {
                    "wall_clock_seconds": None,
                    "active_agent_seconds": None,
                    "playback_wall_seconds": temporal["watched_seconds"],
                },
            )
        ),
        "predicate_results": predicate_results,
    }
    outcome = {
        "status": outcome_status,
        "exact_success": exact_success,
        "disturbance_free_success": disturbance_free_success,
        "task_positive_progress": task_positive,
        "critical_incident": critical_incident,
    }
    evaluated = deepcopy(trace)
    evaluated["watched_intervals"] = watched_intervals
    evaluated["final_oracle_state"] = state
    evaluated["side_effects"] = side_effects
    evaluated["metrics"] = metrics
    evaluated["passed"] = disturbance_free_success
    evaluated["errors"] = list(trace.get("errors", [])) + replay_errors
    evaluated["step_results"] = step_results
    evaluated["dimensions"] = dimensions
    evaluated["outcome"] = outcome
    evaluated["recovery_attempts"] = recovery_attempts
    evaluated["trace_valid"] = trace_valid
    result = {
        "schema_version": RESULT_SCHEMA_VERSION_V2,
        "run_id": trace["run_id"],
        "task_id": task["id"],
        "task_revision": task["revision"],
        "mode": trace["mode"],
        "agent": trace["agent"],
        "benchmark_git_revision": trace["benchmark_git_revision"],
        "benchmark_git_dirty": trace["benchmark_git_dirty"],
        "passed": disturbance_free_success,
        "outcome": outcome,
        "dimensions": dimensions,
        "step_results": step_results,
        "metrics": metrics,
        "side_effects": side_effects,
        "errors": evaluated["errors"],
    }
    return evaluated, result


class FixtureSession:
    def __init__(
        self,
        task: dict[str, Any],
        mode: str,
        agent: str,
        *,
        run_id: str | None = None,
        benchmark_revision: str | None = None,
        benchmark_dirty: bool | None = None,
        execution_surface: dict[str, Any] | None = None,
        trace_version: str = TRACE_SCHEMA_VERSION,
    ) -> None:
        if mode not in task["supported_modes"]:
            raise ValueError(f"{task['id']} does not support mode {mode}")
        if trace_version not in {TRACE_SCHEMA_VERSION, TRACE_SCHEMA_VERSION_V2}:
            raise ValueError(f"unsupported executable trace version: {trace_version}")
        self.task = task
        self.mode = mode
        self.agent = agent
        self.run_id = run_id or str(uuid.uuid4())
        self.benchmark_revision = benchmark_revision
        self.benchmark_dirty = benchmark_dirty
        self.execution_surface = deepcopy(execution_surface)
        self.trace_version = trace_version
        self.started_at = utc_now()
        self.state = deepcopy(task["initial_state"])
        self._id_counters: dict[str, int] = {}
        self.actions: list[dict[str, Any]] = []
        self.observations: list[dict[str, Any]] = []
        self.browser_tool_calls: list[dict[str, Any]] = []
        self.watched_intervals: list[dict[str, Any]] = []
        self.transcript_cues_used: list[str] = []
        self.chapter_ids_used: list[str] = []
        self.dom_player_state_reads: list[dict[str, Any]] = []
        self.verifications: list[str] = []
        self.final_answer: Any = None
        self.screenshots: list[str] = []
        self.errors: list[str] = []
        self.state_snapshots: list[dict[str, Any]] = []
        self.failures: list[dict[str, Any]] = []
        self.recovery_attempts: list[dict[str, Any]] = []
        self.final_verification: dict[str, Any] = {"checks": []}
        self.qualitative_report: dict[str, Any] = {
            "evidence_refs": [],
            "state_uncertainty": None,
            "failure_notes": None,
            "recovery_notes": None,
        }
        if self.trace_version == TRACE_SCHEMA_VERSION_V2:
            self._record_snapshot("initial")

    def _next_id(self, prefix: str) -> str:
        self._id_counters[prefix] = self._id_counters.get(prefix, 0) + 1
        return f"{prefix}-{self._id_counters[prefix]:04d}"

    def _record_snapshot(self, phase: str) -> None:
        if self.trace_version != TRACE_SCHEMA_VERSION_V2:
            return
        self.state_snapshots.append(
            {
                "snapshot_id": self._next_id("snapshot"),
                "sequence": len(self.actions),
                "phase": phase,
                "captured_at": utc_now(),
                "state": deepcopy(self.state),
            }
        )

    def _record_observation(self, value: dict[str, Any]) -> dict[str, Any]:
        observation = deepcopy(value)
        observation.setdefault("sequence", len(self.actions))
        observation.setdefault("timestamp", utc_now())
        if self.trace_version == TRACE_SCHEMA_VERSION_V2:
            observation.setdefault("observation_id", self._next_id("observation"))
        self.observations.append(observation)
        return observation

    def _view_payload(self) -> dict[str, Any]:
        view = agent_view(self.task, self.state, self.mode)
        if self.trace_version == TRACE_SCHEMA_VERSION_V2:
            view["event_log"] = {
                "actions": [
                    {
                        "action_id": row.get("action_id"),
                        "action_type": row.get("type"),
                    }
                    for row in self.actions[-20:]
                ],
                "observations": [
                    {
                        "observation_id": row.get("observation_id"),
                        "channel": row.get("channel"),
                    }
                    for row in self.observations[-20:]
                ],
            }
        return view

    def reset(self) -> None:
        self.__init__(
            self.task,
            self.mode,
            self.agent,
            run_id=self.run_id,
            benchmark_revision=self.benchmark_revision,
            benchmark_dirty=self.benchmark_dirty,
            execution_surface=self.execution_surface,
            trace_version=self.trace_version,
        )

    def view(self) -> dict[str, Any]:
        channel = (
            "dom_player_state"
            if self.mode in {"instrumented_browser", "hybrid"}
            else "screenshot"
        )
        observation = self._record_observation({
            "sequence": len(self.actions),
            "channel": channel,
            "timestamp": utc_now(),
        })
        if channel == "dom_player_state":
            self.dom_player_state_reads.append(
                {"sequence": len(self.actions), "players": deepcopy(self.state["players"])}
            )
        return self._view_payload()

    def apply(self, action: dict[str, Any], *, source: str = "browser") -> dict[str, Any]:
        copied = deepcopy(action)
        if self.trace_version == TRACE_SCHEMA_VERSION_V2:
            copied["action_id"] = self._next_id("action")
            copied["timestamp"] = utc_now()
        self.actions.append(copied)
        tool_call = {
            "sequence": len(self.actions),
            "source": source,
            "name": copied.get("type"),
            "timestamp": utc_now(),
        }
        if self.trace_version == TRACE_SCHEMA_VERSION_V2:
            tool_call["tool_call_id"] = self._next_id("tool-call")
            tool_call["related_action_id"] = copied["action_id"]
        self.browser_tool_calls.append(tool_call)
        try:
            watched, observations, cues, chapters = _apply_action(
                self.task, self.state, copied, self.mode
            )
            self.watched_intervals.extend(watched)
            for row in observations:
                self._record_observation(
                    {
                    "sequence": len(self.actions),
                    "timestamp": utc_now(),
                    **row,
                    }
                )
            self.transcript_cues_used.extend(cues)
            self.chapter_ids_used.extend(chapters)
            if copied.get("type") == "verify" and copied.get("name"):
                self.verifications.append(str(copied["name"]))
            if source == "browser":
                render_channel = (
                    "dom_player_state"
                    if self.mode in {"instrumented_browser", "hybrid"}
                    else "screenshot"
                )
                self._record_observation(
                    {
                        "sequence": len(self.actions),
                        "timestamp": utc_now(),
                        "channel": render_channel,
                        "details": {"post_action_render": True},
                    }
                )
                if render_channel == "dom_player_state":
                    self.dom_player_state_reads.append(
                        {
                            "sequence": len(self.actions),
                            "players": deepcopy(self.state["players"]),
                        }
                    )
            self._record_snapshot("post_action")
        except (KeyError, TypeError, ValueError) as error:
            self.errors.append(str(error))
            if self.trace_version == TRACE_SCHEMA_VERSION_V2:
                self.failures.append(
                    {
                        "failure_id": self._next_id("failure"),
                        "type": "invalid_action",
                        "stage": "action",
                        "summary": str(error),
                        "recoverable": True,
                        "related_action_id": copied.get("action_id"),
                        "related_tool_call_id": tool_call.get("tool_call_id"),
                        "evidence_observation_ids": [],
                    }
                )
                self._record_snapshot("invalid_action")
            raise
        return self._view_payload()

    def submit(
        self,
        answer: Any,
        verifications: list[str] | None = None,
        qualitative_report: dict[str, Any] | None = None,
    ) -> None:
        self.final_answer = answer
        if self.trace_version == TRACE_SCHEMA_VERSION_V2:
            accepted = set(
                self.task["success"].get("accepted_evidence_channels", [])
            )
            available_channels = EXECUTABLE_MODE_CHANNELS[self.mode]
            evidence_channel = next(
                (
                    channel
                    for channel in (
                        "dom_player_state",
                        "player_state",
                        "screenshot",
                        "transcript",
                        "chapters",
                        "video_observation",
                        "audit_log",
                    )
                    if channel in accepted and channel in available_channels
                ),
                None,
            )
            for verification in verifications or []:
                if verification in self.verifications:
                    continue
                self.apply(
                    {
                        "type": "verify",
                        "name": verification,
                        "channel": evidence_channel or "screenshot",
                    },
                    source="browser-submission",
                )
            checks = []
            for verification in self.verifications:
                sequences = [
                    index
                    for index, action in enumerate(self.actions, 1)
                    if action.get("type") == "verify"
                    and action.get("name") == verification
                ]
                evidence_ids = [
                    str(row["observation_id"])
                    for row in self.observations
                    if row.get("sequence") in sequences
                    and row.get("channel") in accepted
                    and row.get("observation_id")
                ]
                checks.append(
                    {
                        "requirement": verification,
                        "evidence_observation_ids": evidence_ids,
                    }
                )
            self.final_verification = {
                "checks": checks
            }
            report = qualitative_report or {}
            refs = report.get("evidence_refs", [])
            if isinstance(refs, str):
                refs = [value.strip() for value in refs.split(",") if value.strip()]
            self.qualitative_report = {
                "evidence_refs": refs if isinstance(refs, list) else [],
                "state_uncertainty": report.get("state_uncertainty"),
                "failure_notes": report.get("failure_notes"),
                "recovery_notes": report.get("recovery_notes"),
            }
            self._record_snapshot("submitted")
        else:
            for verification in verifications or []:
                if verification not in self.verifications:
                    self.verifications.append(verification)

    def trace(self) -> dict[str, Any]:
        revision, dirty = (
            (self.benchmark_revision, self.benchmark_dirty)
            if self.benchmark_revision is not None
            else benchmark_provenance()
        )
        raw = {
            "schema_version": self.trace_version,
            "run_id": self.run_id,
            "task_id": self.task["id"],
            "task_revision": self.task["revision"],
            "mode": self.mode,
            "agent": self.agent,
            "benchmark_git_revision": revision,
            "benchmark_git_dirty": dirty,
            "started_at": self.started_at,
            "ended_at": utc_now(),
            "observations": deepcopy(self.observations),
            "screenshots": deepcopy(self.screenshots),
            "actions": deepcopy(self.actions),
            "browser_tool_calls": deepcopy(self.browser_tool_calls),
            "watched_intervals": deepcopy(self.watched_intervals),
            "transcript_cues_used": deepcopy(self.transcript_cues_used),
            "chapter_ids_used": deepcopy(self.chapter_ids_used),
            "dom_player_state_reads": deepcopy(self.dom_player_state_reads),
            "verifications": deepcopy(self.verifications),
            "final_answer": deepcopy(self.final_answer),
            "final_oracle_state": {},
            "side_effects": {},
            "metrics": {},
            "passed": False,
            "errors": deepcopy(self.errors),
        }
        if self.execution_surface is not None:
            raw["execution_surface"] = deepcopy(self.execution_surface)
        if self.trace_version == TRACE_SCHEMA_VERSION_V2:
            raw.update(
                {
                    "state_snapshots": deepcopy(self.state_snapshots),
                    "failures": deepcopy(self.failures),
                    "recovery_attempts": deepcopy(self.recovery_attempts),
                    "final_verification": deepcopy(self.final_verification),
                    "qualitative_report": deepcopy(self.qualitative_report),
                    "step_results": [],
                    "dimensions": {},
                    "outcome": {
                        "status": "invalid",
                        "exact_success": False,
                        "disturbance_free_success": False,
                        "task_positive_progress": False,
                        "critical_incident": False,
                    },
                    "trace_valid": False,
                }
            )
        evaluated, _ = evaluate_executable_trace(self.task, raw)
        return evaluated

    def oracle_state(self) -> dict[str, Any]:
        return deepcopy(self.state)


def _run_scripted(task: dict[str, Any], mode: str, agent: str) -> FixtureSession:
    session = FixtureSession(task, mode, agent)
    scripted = task["scripted_run"]
    for observation in scripted.get("observations", []):
        session.observations.append(
            {
                "sequence": len(session.actions),
                "timestamp": utc_now(),
                **deepcopy(observation),
            }
        )
        if observation.get("cue_id"):
            session.transcript_cues_used.append(str(observation["cue_id"]))
        if observation.get("chapter_id"):
            session.chapter_ids_used.append(str(observation["chapter_id"]))
    for action in scripted["actions"]:
        session.apply(action, source="scripted-baseline")
    session.submit(
        scripted.get("final_answer"),
        scripted.get("verifications", []),
    )
    return session


def run_executable_suite(
    tasks: list[dict[str, Any]],
    *,
    agent: str,
    seed: int,
    output: Path,
    task_ids: list[str] | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    random.seed(seed)
    selected = [
        task for task in tasks if not task_ids or task["id"] in set(task_ids)
    ]
    missing = sorted(set(task_ids or []) - {task["id"] for task in selected})
    if missing:
        raise ValueError(f"unknown executable task ids: {', '.join(missing)}")
    output.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    revision, dirty = benchmark_provenance()
    results: list[dict[str, Any]] = []
    trace_paths: list[str] = []
    for task in selected:
        selected_mode = mode or task["default_mode"]
        if selected_mode not in task["supported_modes"]:
            selected_mode = task["default_mode"]
        if agent == "scripted":
            session = _run_scripted(task, selected_mode, agent)
        elif agent == "transcript-only" and task["scripted_run"].get(
            "transcript_only_eligible", False
        ):
            session = _run_scripted(task, selected_mode, agent)
        else:
            session = FixtureSession(task, selected_mode, agent)
            if agent == "random" and task.get("random_actions"):
                session.apply(random.choice(task["random_actions"]), source="random-baseline")
            session.submit(None, [])
        trace = session.trace()
        evaluated, result = evaluate_executable_trace(task, trace)
        task_dir = output / task["id"]
        write_json(task_dir / "trace.json", evaluated)
        write_json(task_dir / "result.json", result)
        results.append(result)
        trace_paths.append(str((task_dir / "trace.json").relative_to(output)))
    manifest = {
        "schema_version": "tubecontrol-executable-run.v0.1",
        "run_id": str(uuid.uuid4()),
        "suite": SUITE_ID,
        "started_at": started_at,
        "finished_at": utc_now(),
        "benchmark_version": __version__,
        "benchmark_git_revision": revision,
        "benchmark_git_dirty": dirty,
        "catalog_digest": catalog_digest(tasks),
        "agent": agent,
        "seed": seed,
        "task_count": len(selected),
        "passed": sum(int(row["passed"]) for row in results),
        "failed": sum(int(not row["passed"]) for row in results),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "trace_paths": trace_paths,
    }
    write_json(output / "manifest.json", manifest)
    write_json(output / "results.json", results)
    return manifest


def score_trace_file(
    trace_path: Path,
    output_path: Path | None = None,
    catalog_path: Path | None = None,
) -> dict[str, Any]:
    trace = read_json(trace_path)
    trace_errors = validate_executable_trace(trace)
    if trace_errors:
        raise ValueError("\n".join(trace_errors))
    tasks = load_executable_catalog(catalog_path)
    task_by_id = {task["id"]: task for task in tasks}
    task = task_by_id.get(trace.get("task_id"))
    if task is None:
        raise ValueError(f"unknown task id in trace: {trace.get('task_id')}")
    evaluated, result = evaluate_executable_trace(task, trace)
    if output_path:
        write_json(output_path, evaluated)
    return result


def _static_trace_validation_errors(trace: dict[str, Any]) -> list[str]:
    errors = validate_executable_trace(trace)
    if trace.get("task_id") != "TCE-002":
        errors.append("static trace task_id must be TCE-002")
    if trace.get("mode") != "gui_native":
        errors.append("static trace mode must be gui_native")
    execution_surface = trace.get("execution_surface")
    if not isinstance(execution_surface, dict):
        return errors
    if execution_surface.get("type") != "manual":
        errors.append("static trace execution_surface.type must be manual")
    fixture_version = execution_surface.get("fixture_version")
    if not isinstance(fixture_version, str) or not fixture_version.startswith(
        "codextubebench-static-fixture.v"
    ):
        errors.append("static trace fixture_version is invalid")
    public_url = execution_surface.get("public_url")
    if isinstance(public_url, str):
        parsed = urlsplit(public_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            errors.append(
                "static trace public_url must omit credentials, query, and fragment"
            )
    return errors


def _empty_static_result(errors: list[str]) -> dict[str, Any]:
    return {
        "schema_version": STATIC_RESULT_SCHEMA_VERSION,
        "trace_id": None,
        "task_id": None,
        "fixture_revision": None,
        "fixture_version": None,
        "valid": False,
        "passed": False,
        "metrics": {},
        "side_effects": {},
        "errors": errors,
        "failure_category": "trace_validation_failure",
    }


def score_static_trace_file(
    trace_path: Path,
    output_path: Path,
    catalog_path: Path | None = None,
) -> tuple[dict[str, Any], bool]:
    try:
        trace = read_json(trace_path)
    except (OSError, json.JSONDecodeError) as error:
        result = _empty_static_result([f"could not read static trace: {error}"])
        write_json(output_path, result)
        return result, False
    if not isinstance(trace, dict):
        result = _empty_static_result(["static trace root must be an object"])
        write_json(output_path, result)
        return result, False

    execution_surface = trace.get("execution_surface")
    fixture_version = (
        execution_surface.get("fixture_version")
        if isinstance(execution_surface, dict)
        else None
    )
    result = _empty_static_result([])
    result.update(
        {
            "trace_id": trace.get("run_id"),
            "task_id": trace.get("task_id"),
            "fixture_revision": trace.get("benchmark_git_revision"),
            "fixture_version": fixture_version,
        }
    )
    validation_errors = _static_trace_validation_errors(trace)
    if validation_errors:
        result["errors"] = validation_errors
        write_json(output_path, result)
        return result, False

    tasks = load_executable_catalog(catalog_path)
    task = next((row for row in tasks if row["id"] == "TCE-002"), None)
    if task is None:
        result["errors"] = ["TCE-002 is missing from the executable catalog"]
        write_json(output_path, result)
        return result, False

    _, executable_result = evaluate_executable_trace(task, trace)
    metrics = executable_result["metrics"]
    side_effects = executable_result["side_effects"]
    errors = executable_result["errors"]
    failure_category: str | None = None
    if errors:
        failure_category = "trace_replay_failure"
    elif side_effects["incident_count"]:
        failure_category = "side_effect_failure"
    elif metrics["verification_score"] < 1.0:
        failure_category = "verification_failure"
    elif not executable_result["passed"]:
        failure_category = "task_state_failure"

    passed = executable_result["passed"] and failure_category is None
    result.update(
        {
            "valid": True,
            "passed": passed,
            "metrics": metrics,
            "side_effects": side_effects,
            "errors": errors,
            "failure_category": failure_category,
        }
    )
    write_json(output_path, result)
    return result, True
