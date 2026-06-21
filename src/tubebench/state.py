from __future__ import annotations

from copy import deepcopy
from typing import Any


def get_path(state: dict[str, Any], path: str) -> Any:
    current: Any = state
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def set_path(state: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = state
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = deepcopy(value)


def changed_paths(before: dict[str, Any], after: dict[str, Any], prefix: str = "") -> set[str]:
    paths: set[str] = set()
    keys = set(before) | set(after)
    for key in keys:
        path = f"{prefix}.{key}" if prefix else key
        left, right = before.get(key), after.get(key)
        if isinstance(left, dict) and isinstance(right, dict):
            paths |= changed_paths(left, right, path)
        elif left != right:
            paths.add(path)
    return paths
