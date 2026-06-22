# Reproducibility Checklist

## Run provenance

- [ ] Benchmark Git SHA and dirty status.
- [ ] Lab Git SHA and dirty status.
- [ ] Task ID and revision.
- [ ] Catalog digest.
- [ ] Fixture ID, revision, media checksums, reset version, and oracle version.
- [ ] Evaluator IDs and versions.
- [ ] Access-mode policy digest.
- [ ] Agent and prompt/configuration digests.
- [ ] Random seed and task-order seed.

## Environment

- [ ] Browser and driver versions.
- [ ] Operating system and architecture.
- [ ] Locale, timezone, viewport, device scale, and audio settings.
- [ ] Clock rate and any debug acceleration.
- [ ] Network policy and allowed domains.
- [ ] Clean isolated browser profile.

## Model

- [ ] Exact model identifier and dated release/API version.
- [ ] Sampling and reasoning settings.
- [ ] Tool definitions and access policy.
- [ ] Input/output/cached/reasoning token telemetry when available.
- [ ] Dated pricing source or provider-reported cost.

## Tasks and fixtures

- [ ] License and publication permission.
- [ ] Independent relevant-span annotation.
- [ ] At least two valid strategies documented where applicable.
- [ ] Three consecutive successful resets.
- [ ] Oracle positive and negative controls.
- [ ] Forbidden-action positive and negative tests.
- [ ] Human completion rate and ambiguity review.

## Evaluation

- [ ] Pre-state, trajectory, and post-state audit.
- [ ] Unique and repeated watched intervals.
- [ ] Channel-use and denied-channel events.
- [ ] Verification obligations.
- [ ] Transient and restored side effects.
- [ ] Missing telemetry represented as `null`, never zero.
- [ ] Infrastructure failures separated from agent failures.
- [ ] At least five repetitions for reported stochastic systems.

## Release

- [ ] Aggregate generation command recorded.
- [ ] Aggregate bundle checksums.
- [ ] Raw traces excluded from paper repository.
- [ ] Secret, path, account, and metadata scan.
- [ ] Live-task drift and stale-task report.
- [ ] Deterministic paper generation from aggregate-only inputs.
- [ ] Reproduction from a clean credential-free clone.

The current bootstrap checkout must receive real commits before any non-mock
experiment is treated as research evidence. `uncommitted` provenance is
acceptable only for local development and smoke testing.
