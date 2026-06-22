from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from .intervals import intersect_intervals, interval_duration, normalize_intervals


def _group_spans(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["media_id"])].append(row)
    return grouped


def temporal_observation_metrics(
    media_durations: Mapping[str, float],
    watched_intervals: Iterable[Mapping[str, Any]],
    relevant_spans: Iterable[Mapping[str, Any]],
) -> dict[str, float | None]:
    watched_by_media = _group_spans(watched_intervals)
    relevant_by_media = _group_spans(relevant_spans)
    total_available = 0.0
    total_watched = 0.0
    total_relevant = 0.0
    relevant_watched = 0.0

    unknown = (set(watched_by_media) | set(relevant_by_media)) - set(media_durations)
    if unknown:
        raise ValueError(f"unknown media ids: {', '.join(sorted(unknown))}")

    for media_id, raw_duration in media_durations.items():
        duration = float(raw_duration)
        if not math.isfinite(duration) or duration < 0:
            raise ValueError(f"invalid duration for {media_id}: {raw_duration}")
        watched = normalize_intervals(
            watched_by_media.get(media_id, []),
            duration_seconds=duration,
        )
        relevant = normalize_intervals(
            relevant_by_media.get(media_id, []),
            duration_seconds=duration,
        )
        total_available += duration
        total_watched += interval_duration(watched)
        total_relevant += interval_duration(relevant)
        relevant_watched += interval_duration(intersect_intervals(watched, relevant))

    watch_ratio = total_watched / total_available if total_available else None
    relevant_watch_ratio = relevant_watched / total_watched if total_watched else None
    evidence_coverage = relevant_watched / total_relevant if total_relevant else None
    unnecessary_watched = max(0.0, total_watched - relevant_watched)
    over_observation_score = unnecessary_watched / total_watched if total_watched else 0.0
    under_observation_score = (
        max(0.0, 1.0 - evidence_coverage)
        if evidence_coverage is not None
        else 0.0
    )
    return {
        "available_media_seconds": round(total_available, 6),
        "watched_seconds": round(total_watched, 6),
        "relevant_seconds": round(total_relevant, 6),
        "relevant_watched_seconds": round(relevant_watched, 6),
        "watch_ratio": _rounded(watch_ratio),
        "relevant_watch_ratio": _rounded(relevant_watch_ratio),
        "evidence_coverage": _rounded(evidence_coverage),
        "over_observation_score": round(over_observation_score, 6),
        "under_observation_score": round(under_observation_score, 6),
    }


def timestamp_localization_error(
    predicted_seconds: float,
    target_spans: Iterable[Mapping[str, Any]],
) -> float | None:
    targets = normalize_intervals(target_spans)
    if not targets:
        return None
    predicted = float(predicted_seconds)
    if not math.isfinite(predicted):
        raise ValueError("predicted_seconds must be finite")
    errors = []
    for start, end in targets:
        if start <= predicted <= end:
            errors.append(0.0)
        else:
            errors.append(min(abs(predicted - start), abs(predicted - end)))
    return round(min(errors), 6)


def weighted_efficiency(
    *,
    success: bool,
    actual: Mapping[str, float],
    reference: Mapping[str, float],
    weights: Mapping[str, float] | None = None,
) -> float:
    if not success:
        return 0.0
    selected = weights or {key: 1.0 for key in reference}
    if not selected or any(weight < 0 for weight in selected.values()):
        raise ValueError("weights must be non-negative and non-empty")
    ratios: list[tuple[float, float]] = []
    for key, weight in selected.items():
        if weight == 0:
            continue
        reference_value = float(reference[key])
        actual_value = float(actual[key])
        if reference_value < 0 or actual_value < 0:
            raise ValueError(f"efficiency values for {key} must be non-negative")
        if actual_value == 0:
            ratio = 1.0 if reference_value == 0 else 1.0
        else:
            ratio = min(1.0, reference_value / actual_value)
        ratios.append((ratio, weight))
    if not ratios:
        raise ValueError("at least one positive-weight efficiency dimension is required")
    epsilon = 1e-12
    total_weight = sum(weight for _, weight in ratios)
    score = math.exp(
        sum(weight * math.log(max(ratio, epsilon)) for ratio, weight in ratios)
        / total_weight
    )
    return round(score, 6)


def requirement_score(required: Iterable[str], observed: Iterable[str]) -> float:
    required_set = set(required)
    if not required_set:
        return 1.0
    return round(len(required_set & set(observed)) / len(required_set), 6)


def _rounded(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None
