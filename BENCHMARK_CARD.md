# TubeBench Benchmark Card

## Purpose

TubeBench evaluates browser-use agents on long-form video tasks. It records the
trajectory needed to distinguish task completion from grounded completion,
verification quality, side effects, restoration, temporal error, and runtime
or environment blockers.

This repository provides benchmark infrastructure and bounded experimental
evidence. It does not establish general browser-agent competence.

## Tracks and evidence

### Deterministic diagnostics

The 24-task `tubecontrol` catalog and mock adapters validate evaluator,
trajectory, and aggregate behavior. Their frozen paper rows are synthetic
controls, not deployed-agent results.

### Deterministic fixture

The 12-task executable catalog provides benchmark-owned state, exact reset,
trace replay, protected-state checks, and an evaluator-only oracle. Hosted
sessions add stable step/evidence identifiers, failure and recovery records,
and separate correctness, grounding, verification, safety, temporal, and
efficiency dimensions without a single partial-credit composite. Retained
TCE-002 traces are protocol validation; repeated task-complete results have not
yet been reported.

### Live YouTube

The 12-task catalog defines future signed-out, read-only pilots on public
YouTube pages. Pages and UI state are volatile. No live YouTube-only aggregate
is currently approved for publication.

### Live public video

The 24-task catalog covers YouTube, MIT OpenCourseWare, C-SPAN, Internet
Archive, and Library of Congress pages. The June 30, 2026 pilot retained all 24
slots, completed 22, and blocked 2. The independent July 14, 2026 campaign
retained 72 attempts, completed 63, and classified 9 as partial. The same three
timestamp-localization tasks were partial in all three repetitions.

The live-public results apply only to their dated browser/model configuration.
They are not pooled with each other or with fixture results, and do not support
cross-agent, leaderboard, or general competence claims.

## Current task assets

- `benchmarks/tubecontrol/tasks/catalog.json`: 24 diagnostic tasks;
- `benchmarks/tubecontrol_executable_v0/tasks/catalog.json`: 12 deterministic
  executable tasks;
- `benchmarks/live_youtube_v0/tasks/catalog.json`: 12 live YouTube contracts;
- `benchmarks/live_public_video_v0/tasks/catalog.json`: 24 live-public
  contracts.

## Metrics

Metrics include exact and disturbance-free success, state and answer atoms,
evidence-linked grounding, verification, step usefulness/validity, side-effect
incidents, state restoration, recovery, timestamp localization error, watch
coverage, and ungated reference efficiency. Implementation status is documented in
[docs/metrics.md](docs/metrics.md).

## Evidence and privacy boundary

Raw live traces, screenshots, observations, page text, browser state, profiles,
cookies, tokens, account data, and transcript dumps remain private lab
evidence. The paper repository receives reviewed aggregates containing only
allowlisted, redacted fields.

Blocked, partial, failed, and invalid retained attempts are not silently
replaced. Diagnostic, protocol-validation, pilot, and repeated-campaign labels
remain explicit in every report.

## Exclusions

Public tasks do not authorize account mutation, engagement actions, posting,
purchases, moderation, downloads, ad interaction, login, or use of personal
browser profiles. Public write-action tasks require benchmark-owned fixtures.

## Known limitations

The deterministic player uses a virtual media timeline rather than decoded
audiovisual content. Live pages drift. Browser/controller normalization,
generic restoration scoring, automatic failure labeling, provider-driven
repeated execution, and complete cost/latency telemetry remain incomplete.

## Non-affiliation

TubeBench is independent and is not affiliated with, endorsed by, or sponsored
by YouTube, Google, or OpenAI.
