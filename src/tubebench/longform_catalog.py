from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json
from .modes import MODE_CHANNELS, validate_mode_channels

REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "track",
    "revision",
    "tier",
    "category",
    "title",
    "instruction",
    "environment",
    "mode_policies",
    "media",
    "ground_truth",
    "actions",
    "evaluation",
    "human_reference",
    "budgets",
    "safety",
}


def default_longform_catalog_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "benchmarks/longform_seed/tasks/catalog.json"
    )


def load_longform_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    value = read_json(path or default_longform_catalog_path())
    if not isinstance(value, list):
        raise ValueError("long-form catalog root must be a JSON array")
    return value


def validate_longform_catalog(tasks: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, task in enumerate(tasks):
        label = task.get("id", f"index {index}")
        missing = sorted(REQUIRED_FIELDS - task.keys())
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
            continue
        task_id = task["id"]
        if task_id in seen:
            errors.append(f"{label}: duplicate task id")
        seen.add(task_id)
        if task["schema_version"] != "1.0":
            errors.append(f"{label}: schema_version must be 1.0")
        if task["track"] != "longform_media":
            errors.append(f"{label}: track must be longform_media")
        if task["tier"] not in {"L1", "L2", "L3", "L4"}:
            errors.append(f"{label}: invalid tier")
        if not isinstance(task["revision"], int) or task["revision"] < 1:
            errors.append(f"{label}: revision must be a positive integer")

        environment = task["environment"]
        if environment.get("stability") not in {"verified", "live"}:
            errors.append(f"{label}: environment stability must be verified or live")
        supported_modes = environment.get("supported_modes", [])
        default_mode = environment.get("default_mode")
        if default_mode not in supported_modes:
            errors.append(f"{label}: default_mode must be supported")
        if set(supported_modes) - set(MODE_CHANNELS):
            errors.append(f"{label}: unsupported environment mode")
        policies = task["mode_policies"]
        if set(policies) != set(supported_modes):
            errors.append(f"{label}: mode_policies must exactly match supported_modes")
        for mode, policy in policies.items():
            errors.extend(
                f"{label}: {error}"
                for error in validate_mode_channels(mode, policy.get("allowed_channels", []))
            )
            if not isinstance(policy.get("forbidden_channels"), list):
                errors.append(f"{label}: {mode} forbidden_channels must be a list")

        media_rows = task["media"]
        media_ids = {row.get("media_id") for row in media_rows}
        if not media_rows or None in media_ids or len(media_ids) != len(media_rows):
            errors.append(f"{label}: media ids must be present and unique")
        for row in media_rows:
            duration = row.get("duration_seconds")
            if not isinstance(duration, (int, float)) or duration <= 0:
                errors.append(f"{label}: media duration must be positive")
        for span in task["ground_truth"].get("relevant_spans", []):
            if span.get("media_id") not in media_ids:
                errors.append(f"{label}: relevant span references unknown media")
            start = span.get("start_seconds")
            end = span.get("end_seconds")
            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                errors.append(f"{label}: relevant span boundaries must be numeric")
            elif end <= start:
                errors.append(f"{label}: relevant span must have positive duration")
        obligations = task["ground_truth"].get("evidence_obligations")
        if not isinstance(obligations, list) or not obligations:
            errors.append(f"{label}: at least one evidence obligation is required")
        else:
            obligation_ids: set[str] = set()
            for obligation in obligations:
                obligation_id = obligation.get("id")
                if not isinstance(obligation_id, str) or not obligation_id:
                    errors.append(f"{label}: evidence obligation id is required")
                elif obligation_id in obligation_ids:
                    errors.append(f"{label}: duplicate evidence obligation id")
                else:
                    obligation_ids.add(obligation_id)
                alternatives = obligation.get("alternatives")
                if not isinstance(alternatives, list) or not alternatives:
                    errors.append(f"{label}: evidence alternatives are required")
                    continue
                for alternative in alternatives:
                    if not isinstance(alternative, list) or not alternative:
                        errors.append(f"{label}: evidence alternative must contain atoms")
                        continue
                    for atom in alternative:
                        if not isinstance(atom.get("channel"), str):
                            errors.append(f"{label}: evidence atom channel is required")
                        if atom.get("media_id") not in media_ids | {None}:
                            errors.append(f"{label}: evidence atom references unknown media")
                        has_start = "start_seconds" in atom
                        has_end = "end_seconds" in atom
                        if has_start != has_end:
                            errors.append(f"{label}: evidence intervals require start and end")
                        elif has_start and atom["end_seconds"] <= atom["start_seconds"]:
                            errors.append(f"{label}: evidence interval must have positive duration")

        reference = task["human_reference"]
        for field in ("steps", "watched_seconds", "active_seconds"):
            if not isinstance(reference.get(field), (int, float)) or reference[field] < 0:
                errors.append(f"{label}: human_reference.{field} must be non-negative")
        budgets = task["budgets"]
        for field in ("max_steps", "max_watch_seconds", "max_wall_clock_seconds"):
            if not isinstance(budgets.get(field), (int, float)) or budgets[field] <= 0:
                errors.append(f"{label}: budgets.{field} must be positive")
    if not 10 <= len(tasks) <= 50:
        errors.append(f"seed catalog must contain 10-50 tasks; found {len(tasks)}")
    return errors
