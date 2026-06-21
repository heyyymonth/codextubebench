from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json

REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "track",
    "mode",
    "title",
    "goal",
    "risk_level",
    "initial_state",
    "success_predicates",
    "allowed_mutations",
    "forbidden_mutations",
    "optimal_steps",
    "mock_actions",
}


def default_catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmarks/tubecontrol/tasks/catalog.json"


def load_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    value = read_json(path or default_catalog_path())
    if not isinstance(value, list):
        raise ValueError("catalog root must be a JSON array")
    return value


def validate_catalog(tasks: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, task in enumerate(tasks):
        label = task.get("id", f"index {index}")
        missing = sorted(REQUIRED_FIELDS - task.keys())
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
        task_id = task.get("id")
        if task_id in seen:
            errors.append(f"{label}: duplicate task id")
        if isinstance(task_id, str):
            seen.add(task_id)
        if task.get("track") != "tubecontrol":
            errors.append(f"{label}: pilot catalog must use track=tubecontrol")
        if task.get("mode") not in {"verified", "live"}:
            errors.append(f"{label}: mode must be verified or live")
        if not isinstance(task.get("optimal_steps"), int) or task.get("optimal_steps", 0) <= 0:
            errors.append(f"{label}: optimal_steps must be a positive integer")
        for field in ("success_predicates", "allowed_mutations", "forbidden_mutations", "mock_actions"):
            if not isinstance(task.get(field), list):
                errors.append(f"{label}: {field} must be a list")
        for predicate in task.get("success_predicates", []):
            if set(predicate) != {"path", "equals"}:
                errors.append(f"{label}: predicates require exactly path and equals")
    if not 20 <= len(tasks) <= 30:
        errors.append(f"pilot catalog must contain 20-30 tasks; found {len(tasks)}")
    return errors
