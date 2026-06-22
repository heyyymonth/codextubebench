import unittest

from tubebench.intervals import intersect_intervals, interval_duration, normalize_intervals
from tubebench.temporal_metrics import (
    requirement_score,
    temporal_observation_metrics,
    timestamp_localization_error,
    weighted_efficiency,
)


class IntervalTests(unittest.TestCase):
    def test_normalizes_clips_and_merges_overlaps(self) -> None:
        spans = normalize_intervals(
            [(-2, 5), (4, 10), (20, 30), (29, 35)],
            duration_seconds=32,
        )
        self.assertEqual([(0.0, 10.0), (20.0, 32)], spans)

    def test_intersection_duration(self) -> None:
        left = normalize_intervals([(0, 10), (20, 30)])
        right = normalize_intervals([(5, 25)])
        self.assertEqual(10.0, interval_duration(intersect_intervals(left, right)))


class TemporalMetricTests(unittest.TestCase):
    def test_observation_metrics_use_interval_unions(self) -> None:
        metrics = temporal_observation_metrics(
            {"a": 100},
            [
                {"media_id": "a", "start_seconds": 0, "end_seconds": 20},
                {"media_id": "a", "start_seconds": 10, "end_seconds": 30},
            ],
            [{"media_id": "a", "start_seconds": 15, "end_seconds": 25}],
        )
        self.assertEqual(30.0, metrics["watched_seconds"])
        self.assertEqual(10.0, metrics["relevant_watched_seconds"])
        self.assertEqual(0.3, metrics["watch_ratio"])
        self.assertEqual(0.333333, metrics["relevant_watch_ratio"])
        self.assertEqual(1.0, metrics["evidence_coverage"])
        self.assertEqual(0.666667, metrics["over_observation_score"])
        self.assertEqual(0.0, metrics["under_observation_score"])

    def test_timestamp_error_is_zero_inside_target_span(self) -> None:
        targets = [{"start_seconds": 40, "end_seconds": 45}]
        self.assertEqual(0.0, timestamp_localization_error(42, targets))
        self.assertEqual(5.0, timestamp_localization_error(50, targets))

    def test_weighted_efficiency_gates_on_success(self) -> None:
        actual = {"steps": 10, "watch_seconds": 60}
        reference = {"steps": 5, "watch_seconds": 30}
        self.assertEqual(
            0.5,
            weighted_efficiency(
                success=True,
                actual=actual,
                reference=reference,
            ),
        )
        self.assertEqual(
            0.0,
            weighted_efficiency(
                success=False,
                actual=actual,
                reference=reference,
            ),
        )

    def test_requirement_score(self) -> None:
        self.assertEqual(0.5, requirement_score(["final_state", "independent_evidence"], ["final_state"]))


if __name__ == "__main__":
    unittest.main()
