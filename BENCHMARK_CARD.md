# TubeBench Benchmark Card

## Scope

TubeBench evaluates browser agents performing operational YouTube tasks:
playback control, temporal navigation, captions, transcripts, playlists,
creator workflows, and disturbance minimization.

The initial artifact contains a 24-task deterministic TubeControl mock/replay
pilot. It validates task/evaluator/trace pipelines; it is not evidence of
performance on the live YouTube website.

## Tracks and modes

- TubeControl: exact deterministic operations.
- TubeWorkflow: composite workflows with exact checks and declared rubrics.
- TubeStudio: controlled creator-side operations on benchmark-owned assets.
- Verified mode: controlled fixtures and exact reset/oracle behavior.
- Live mode: dynamic public content, repeated runs, read-heavy tasks.

Browser-only and hybrid/tool-assisted results are separate comparison classes.

## Primary metrics

- Exact success rate.
- Partial completion.
- Disturbance-free success rate.
- Side-effect incident count.
- Step efficiency against a human or authored reference.
- Wall-clock latency and, when available, tokens and cost.
- Rerun reliability.
- Human/judge agreement for rubric tasks.

## Exclusions

TubeBench does not authorize engagement manipulation, public comment spam,
third-party account changes, purchases, moderation actions, or access to
personal browser profiles. Public live-mode tasks must be read-heavy.

## Known limitations

The mock state model does not reproduce visual grounding, network drift,
advertisements, consent dialogs, experiments, personalization, or full
browser/OS behavior. See `docs/limitations.md`.

## Non-affiliation

TubeBench is an independent research project and is not affiliated with,
endorsed by, or sponsored by YouTube or Google.
