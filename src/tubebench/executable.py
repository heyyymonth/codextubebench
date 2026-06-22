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
    missing = sorted(REQUIRED_TRACE_FIELDS - trace.keys())
    if missing:
        errors.append(f"trace missing fields: {', '.join(missing)}")
    if trace.get("schema_version") != TRACE_SCHEMA_VERSION:
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
    if not isinstance(trace.get("metrics"), dict):
        errors.append("trace.metrics must be an object")
    if not isinstance(trace.get("side_effects"), dict):
        errors.append("trace.side_effects must be an object")
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


class FixtureSession:
    def __init__(
        self,
        task: dict[str, Any],
        mode: str,
        agent: str,
        *,
        run_id: str | None = None,
    ) -> None:
        if mode not in task["supported_modes"]:
            raise ValueError(f"{task['id']} does not support mode {mode}")
        self.task = task
        self.mode = mode
        self.agent = agent
        self.run_id = run_id or str(uuid.uuid4())
        self.started_at = utc_now()
        self.state = deepcopy(task["initial_state"])
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

    def reset(self) -> None:
        self.__init__(self.task, self.mode, self.agent, run_id=self.run_id)

    def view(self) -> dict[str, Any]:
        channel = (
            "dom_player_state"
            if self.mode in {"instrumented_browser", "hybrid"}
            else "screenshot"
        )
        observation = {
            "sequence": len(self.actions),
            "channel": channel,
            "timestamp": utc_now(),
        }
        self.observations.append(observation)
        if channel == "dom_player_state":
            self.dom_player_state_reads.append(
                {"sequence": len(self.actions), "players": deepcopy(self.state["players"])}
            )
        return agent_view(self.task, self.state, self.mode)

    def apply(self, action: dict[str, Any], *, source: str = "browser") -> dict[str, Any]:
        copied = deepcopy(action)
        self.actions.append(copied)
        self.browser_tool_calls.append(
            {
                "sequence": len(self.actions),
                "source": source,
                "name": copied.get("type"),
                "timestamp": utc_now(),
            }
        )
        try:
            watched, observations, cues, chapters = _apply_action(
                self.task, self.state, copied, self.mode
            )
            self.watched_intervals.extend(watched)
            self.observations.extend(
                {
                    "sequence": len(self.actions),
                    "timestamp": utc_now(),
                    **row,
                }
                for row in observations
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
                self.observations.append(
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
        except (KeyError, TypeError, ValueError) as error:
            self.errors.append(str(error))
            raise
        return agent_view(self.task, self.state, self.mode)

    def submit(self, answer: Any, verifications: list[str] | None = None) -> None:
        self.final_answer = answer
        for verification in verifications or []:
            if verification not in self.verifications:
                self.verifications.append(verification)

    def trace(self) -> dict[str, Any]:
        revision, dirty = benchmark_provenance()
        raw = {
            "schema_version": TRACE_SCHEMA_VERSION,
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
