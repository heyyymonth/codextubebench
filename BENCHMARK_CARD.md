# TubeBench Benchmark Card

## Purpose

TubeBench evaluates Codex on YouTube browser-use tasks. It captures what
Codex observes and does, checks whether the requested outcome is achieved, and
classifies failures involving grounding, media state, verification, side
effects, restoration, timestamps, and observation strategy.

This is an empirical evaluation harness, not a claim that Codex has already
been comprehensively benchmarked.

## Tracks

### Deterministic fixture track

- Benchmark-owned YouTube-like local player.
- Exact reset and evaluator-only oracle.
- Reproducible task and trace replay.
- Primary track for repeated scoring and failure reproduction.

### Live YouTube track

- Real public YouTube pages at a recorded date and time.
- Read-only tasks across long videos, live streams, and long music/ambient
  videos.
- Used to discover product-behavior failures and test transfer.
- Non-deterministic and never pooled with fixture results.

### Live public video track

- Real public long-form video pages at a recorded date and time.
- Read-only tasks across YouTube, MIT OpenCourseWare, C-SPAN, Internet
  Archive, and Library of Congress public-domain film pages.
- Used for dimensional browser-use observations across sites, task families,
  evidence coverage, blocked states, and unsupported claims.
- One reviewed dated v0 pilot has been run and reported as aggregate-only
  evidence: 24 retained slots, 22 completed, 2 blocked.
- Non-deterministic and never pooled with fixture results.

## Current task assets

- 12 executable deterministic tasks in
  `benchmarks/tubecontrol_executable_v0/tasks/catalog.json`.
- 12 live YouTube task contracts in
  `benchmarks/live_youtube_v0/tasks/catalog.json`.
- 24 live public video task contracts in
  `benchmarks/live_public_video_v0/tasks/catalog.json`.
- 24 compatibility mock/replay tasks used for evaluator diagnostics.
- 10 schema-level long-form seed contracts that are not executable fixtures.

## Current core metrics

- success;
- step count;
- browser/tool-call count;
- verification score;
- side-effect/disturbance score;
- state restoration score;
- timestamp localization error when applicable;
- watch time/watch ratio when applicable;
- failure category.

State restoration and failure classification are not yet fully automated across
both tracks. See `docs/metrics.md` for exact status.

## Result interpretation

- Mock/replay results are synthetic diagnostics.
- A single local Codex run is protocol validation.
- A one-pass live run is a dated pilot observation.
- The live public video v0 pilot is a formal dated aggregate-only result, not a
  repeated benchmark score.
- A repeated Codex benchmark result requires pinned revisions, a fixed prompt
  and mode, complete task coverage, repeated runs, and aggregate reporting.

## Exclusions

Live tasks do not authorize account mutation, engagement actions, public
posting, purchases, moderation, downloads, ad interaction, login, or use of
personal browser profiles.

## Known limitations

The local fixture uses a virtual media timeline rather than encoded audiovisual
content. Live YouTube pages drift. Full browser/OS side-effect coverage,
provider-driven Codex automation, generic restoration scoring, and complete
cost/latency telemetry are not implemented.

## Non-affiliation

TubeBench is independent and is not affiliated with, endorsed by, or
sponsored by YouTube, Google, or OpenAI.
