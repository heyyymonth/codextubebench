from __future__ import annotations

import hashlib
import json
import platform
import random
import subprocess
import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .evaluator import evaluate
from .io import write_json, write_jsonl
from .state import get_path, set_path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _catalog_digest(tasks: list[dict[str, Any]]) -> str:
    payload = json.dumps(tasks, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _git_provenance() -> tuple[str, bool | None]:
    root = Path(__file__).resolve().parents[2]
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "uncommitted", None
    dirty = bool(subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip())
    return revision, dirty


def _actions_for(task: dict[str, Any], agent: str) -> list[dict[str, Any]]:
    if agent == "mock-perfect":
        return deepcopy(task["mock_actions"])
    if agent == "mock-noop":
        return []
    if agent == "mock-reckless":
        actions = deepcopy(task["mock_actions"])
        if task["forbidden_mutations"]:
            actions.append({
                "path": task["forbidden_mutations"][0],
                "value": "__unintended_change__",
            })
        return actions
    if agent == "mock-transient":
        actions = deepcopy(task["mock_actions"])
        if task["forbidden_mutations"]:
            path = task["forbidden_mutations"][0]
            original = get_path(task["initial_state"], path)
            actions.extend([
                {"path": path, "value": "__temporary_disturbance__"},
                {"path": path, "value": original},
            ])
        return actions
    raise ValueError(f"unsupported agent: {agent}")


def run_suite(
    tasks: list[dict[str, Any]],
    agent: str,
    seed: int,
    output: Path,
) -> dict[str, Any]:
    random.seed(seed)
    benchmark_git_revision, benchmark_git_dirty = _git_provenance()
    run_id = str(uuid.uuid4())
    started = _utc_now()
    results: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for task in tasks:
        before = deepcopy(task["initial_state"])
        after = deepcopy(before)
        actions = _actions_for(task, agent)
        task_started = time.perf_counter()
        traces.append({
            "schema_version": "1.0",
            "run_id": run_id,
            "task_id": task["id"],
            "sequence": 0,
            "event": "task_start",
            "timestamp": _utc_now(),
            "payload": {"initial_state": before},
        })
        for sequence, action in enumerate(actions, 1):
            set_path(after, action["path"], action["value"])
            traces.append({
                "schema_version": "1.0",
                "run_id": run_id,
                "task_id": task["id"],
                "sequence": sequence,
                "event": "action",
                "timestamp": _utc_now(),
                "payload": action,
            })
        metrics = evaluate(
            task,
            before,
            after,
            len(actions),
            action_paths=[action["path"] for action in actions],
        )
        elapsed_ms = round((time.perf_counter() - task_started) * 1000, 3)
        result = {
            "schema_version": "1.0",
            "run_id": run_id,
            "task_id": task["id"],
            "track": task["track"],
            "mode": task["mode"],
            "agent": agent,
            "seed": seed,
            "steps": len(actions),
            "wall_clock_ms": elapsed_ms,
            **metrics,
        }
        results.append(result)
        traces.append({
            "schema_version": "1.0",
            "run_id": run_id,
            "task_id": task["id"],
            "sequence": len(actions) + 1,
            "event": "task_end",
            "timestamp": _utc_now(),
            "payload": {"final_state": after, "result": result},
        })
    manifest = {
        "schema_version": "1.0",
        "run_id": run_id,
        "started_at": started,
        "finished_at": _utc_now(),
        "benchmark_version": __version__,
        "benchmark_git_revision": benchmark_git_revision,
        "benchmark_git_dirty": benchmark_git_dirty,
        "catalog_digest": _catalog_digest(tasks),
        "agent": agent,
        "agent_class": "browser-only-mock",
        "seed": seed,
        "task_count": len(tasks),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    write_json(output / "manifest.json", manifest)
    write_jsonl(output / "results.jsonl", results)
    write_jsonl(output / "trace.jsonl", traces)
    return manifest


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    if not count:
        return {"task_runs": 0}
    key = lambda name: sum(float(row[name]) for row in rows) / count
    return {
        "task_runs": count,
        "exact_success_rate": round(key("exact_success"), 6),
        "partial_completion": round(key("partial_completion"), 6),
        "disturbance_free_success_rate": round(key("disturbance_free_success"), 6),
        "mean_side_effect_score": round(key("side_effect_score"), 6),
        "mean_step_efficiency": round(key("step_efficiency"), 6),
        "mean_wall_clock_ms": round(key("wall_clock_ms"), 6),
    }
