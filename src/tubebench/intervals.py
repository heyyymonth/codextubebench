from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

Interval = tuple[float, float]


def _coerce_interval(span: Mapping[str, Any] | Sequence[float]) -> Interval:
    if isinstance(span, Mapping):
        start = float(span["start_seconds"])
        end = float(span["end_seconds"])
    else:
        start = float(span[0])
        end = float(span[1])
    if not math.isfinite(start) or not math.isfinite(end):
        raise ValueError("interval boundaries must be finite")
    if end < start:
        raise ValueError(f"interval end {end} precedes start {start}")
    return start, end


def normalize_intervals(
    spans: Iterable[Mapping[str, Any] | Sequence[float]],
    *,
    duration_seconds: float | None = None,
) -> list[Interval]:
    if duration_seconds is not None and duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")
    normalized: list[Interval] = []
    for span in spans:
        start, end = _coerce_interval(span)
        if duration_seconds is not None:
            start = min(max(start, 0.0), duration_seconds)
            end = min(max(end, 0.0), duration_seconds)
        if end > start:
            normalized.append((start, end))
    normalized.sort()
    merged: list[Interval] = []
    for start, end in normalized:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def interval_duration(spans: Iterable[Interval]) -> float:
    return sum(end - start for start, end in spans)


def intersect_intervals(left: Iterable[Interval], right: Iterable[Interval]) -> list[Interval]:
    left_rows = list(left)
    right_rows = list(right)
    intersections: list[Interval] = []
    i = 0
    j = 0
    while i < len(left_rows) and j < len(right_rows):
        start = max(left_rows[i][0], right_rows[j][0])
        end = min(left_rows[i][1], right_rows[j][1])
        if end > start:
            intersections.append((start, end))
        if left_rows[i][1] <= right_rows[j][1]:
            i += 1
        else:
            j += 1
    return intersections
