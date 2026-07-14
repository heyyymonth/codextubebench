# TubeBench

TubeBench is a benchmark and evaluation harness for measuring how Codex
performs on YouTube browser-use tasks. It records Codex actions and
observations, scores task completion and side effects, and turns observed
failures into reproducible benchmark cases.

The core question is:

> How well can Codex use YouTube in a browser to complete long-form media
> tasks, and where does it fail?

TubeBench is the benchmark name. The Python package remains `tubebench`
for backward compatibility, and existing catalog/schema identifiers are
preserved. Deployed URLs, `codextubebench-*` schema/fixture IDs,
`CODEXTUBEBENCH_*` environment variables, and `CodexTubeBenchStatic*`
JavaScript globals remain compatibility contracts.

## What is included

- **Deterministic fixture track:** 12 runnable YouTube-like browser tasks with
  reset, trace capture, replay scoring, and protected-state checks.
- **Live YouTube track:** 12 read-only public-page task contracts for dated
  product-behavior pilots.
- **Live public video track:** 24 read-only public-page task contracts across
  YouTube, MIT OCW, C-SPAN, Internet Archive, and Library of Congress pages.
- **Codex protocol:** instructions for running one task, capturing its trace,
  and scoring it without exposing evaluator authority.
- **Trace and result schemas:** actions, observations, browser/tool calls,
  watched intervals, verifications, final state, side effects, and failures.
- **Failure analysis:** a Codex-specific taxonomy linking trace symptoms to
  deterministic reproduction opportunities.
- **Lab handoff:** raw Codex traces stay in `../youtube-benchmark-lab`; only
  sanitized aggregates may enter the report repository.

## Result labels

| Label | Meaning |
| --- | --- |
| Synthetic/mock | Pipeline or evaluator diagnostic; not Codex performance |
| Deterministic fixture | Repeated Codex evaluation on a pinned local fixture |
| Codex protocol validation | One controlled Codex run proving capture/scoring works |
| Live YouTube pilot | Approved, dated, non-deterministic Codex behavior on public YouTube |
| Live public video pilot | Approved, dated, non-deterministic Codex behavior on public long-form video pages |
| Repeated dated live-public campaign | Reviewed repetitions in one dated browser/model configuration; not a deterministic leaderboard |
| Repeated Codex benchmark result | Pinned tasks, fixed mode/prompt, repeated runs, and aggregate reporting |

Current approved empirical live-public evidence includes the unchanged
`live_public_video_v0` 24-slot dated pilot (22 completed, 2 blocked, 0.916667
retained-denominator completion) and the independent
`live-public-video-retained-v1` campaign (72 fresh attempts, 63 completed, 9
partial, 0.875 retained-denominator completion). The latter is a repeated dated
result for one browser/model configuration, not a deterministic leaderboard,
cross-agent comparison, general competence claim, or repeated deterministic
Codex benchmark result. No current artifact is an approved live YouTube-only
result.

## Quick start

Requirements: Python 3.11+. The deterministic core has no third-party runtime
dependencies.

```bash
make test
make validate
make executable-smoke
make release-check
```

The smoke command runs scripted and no-op controls, not Codex.

## Run one deterministic task with Codex

1. Validate and record the benchmark revision:

   ```bash
   git status --short --branch
   git rev-parse HEAD
   make test validate
   ```

2. Start the fixture:

   ```bash
   PYTHONPATH=src python3 -m tubebench.cli serve-fixture --port 8765
   ```

   If the browser cannot access loopback, deploy the same fixture as the
   single-replica OCI service documented in `docs/hosted_fixture.md`. A hosted
   deployment is not currently assumed to exist.

3. Open a task such as:

   ```text
   http://127.0.0.1:8765/?task=TCE-002&mode=gui_native&agent=codex
   ```

4. Follow `docs/codex_evaluation_protocol.md`. Store the exported raw trace
   under the lab repository, then score it:

   ```bash
   PYTHONPATH=src python3 -m tubebench.cli score-executable-trace \
     ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/trace.json \
     --output ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/evaluated-trace.json
   ```

For the TCE-002-only GitHub Pages fallback and its visible manual trace
handoff, use `score-static-trace` as documented in
`docs/github_pages_fixture.md`.

One run is protocol validation. Repeated evaluation is specified in
`docs/next_codex_experiments.md`.

## Tracks

### Deterministic fixture

`benchmarks/tubecontrol_executable_v0/tasks/catalog.json` contains 12 runnable
proxy tasks for YouTube failures such as wrong-tab actions, state restoration,
timestamp localization, transcript/channel use, and verification.

See `docs/deterministic_fixture.md`.
For the gated HTTPS execution surface, see `docs/hosted_fixture.md`.
For the limited static HTTPS fallback, see `docs/github_pages_fixture.md`.
The published TCE-002-only fallback is
`https://heyyymonth.github.io/codextubebench/`.

### Live YouTube

`benchmarks/live_youtube_v0/tasks/catalog.json` contains read-only public-page
tasks spanning long-form educational videos, long music/ambient videos, and
live streams. The catalog defines a planned protocol. Existing private traces
are not approved publication evidence. Any future reviewed live result is
volatile and must never be pooled with fixture results.

See `docs/live_youtube_protocol.md`.

### Live Public Video

`benchmarks/live_public_video_v0/tasks/catalog.json` contains 24 read-only
public-page tasks spanning YouTube, MIT OpenCourseWare, C-SPAN, Internet
Archive, and Library of Congress public-domain film pages. This is a volatile
pilot lane. Raw screenshots and traces stay in the private lab repository, and
blocked slots remain in denominator reporting.

The first reviewed v0 pilot retained all 24 slots on June 30, 2026: 22
completed and 2 blocked. Only aggregate, redacted metrics are exported to the
paper repository; raw screenshots, traces, page text, and observations remain
private lab evidence.

The independent retained-v1 campaign ran 72 fresh slots on July 14, 2026 under
three repetition IDs. It completed 63 attempts and retained 9 partial
timestamp-localization outcomes; no attempt failed, blocked, or became invalid.
Each repetition completed 21 of 24 attempts, and the same three tasks were
partial in all three repetitions. The reviewed export reports complete evidence
and screenshot coverage, zero unsupported claims, and zero side-effect
incidents. The pilot and campaign are not pooled.

See `docs/live_public_video_protocol.md`.

## Metrics

Current Codex evaluation prioritizes:

1. success;
2. step count;
3. browser/tool-call count;
4. verification score;
5. side-effect/disturbance score;
6. state restoration score;
7. timestamp error when applicable;
8. watch time/watch ratio when applicable;
9. failure category.

Relevant watch ratio, over/under-observation, state tracking, information
channel selection, cost, and latency are secondary or future metrics. Exact
implementation status is in `docs/metrics.md`.

## Implemented versus not implemented

Implemented now:

- deterministic catalog validation, fixture server, trace capture, replay
  scoring, exact success, trajectory side effects, verification coverage,
  timestamp error, watch ratio, and step count;
- live task/trace validation and retained lab-side analysis tooling;
- live public video task/trace validation, retained lab-side campaign tooling,
  one reviewed aggregate-only pilot handoff, and one independent reviewed
  aggregate-only 72-attempt campaign handoff;
- release checks for secrets, local paths, and raw browser artifacts.

Partial or not yet automated:

- generic state-restoration ratios, complete browser/tool-call normalization,
  full failure-category assignment, state tracking, channel-efficiency scoring,
  complete cost/latency collection, and a provider-driven repeated Codex runner.

## Source-of-truth docs

- `BENCHMARK_CARD.md`
- `docs/methodology.md`
- `docs/metrics.md`
- `docs/task_taxonomy.md`
- `docs/codex_evaluation_protocol.md`
- `docs/longform_experiment_framework.md`
- `docs/failure_taxonomy.md`
- `docs/deterministic_fixture.md`
- `docs/hosted_fixture.md`
- `docs/github_pages_fixture.md`
- `docs/live_youtube_protocol.md`
- `docs/live_public_video_protocol.md`
- `docs/next_codex_experiments.md`
- `docs/limitations.md`
- `docs/roadmap.md`

Background research material is excluded from source-of-truth docs unless it is
reintroduced through the current benchmark framing.

## Safety and privacy

Live tasks are read-only. Do not like, subscribe, comment, save, donate, chat,
sign in, download media, interact with ads, or mutate accounts. Never commit
credentials, cookies, browser profiles, account identifiers, raw authenticated
captures, unrelated tabs, or full third-party transcripts.

TubeBench is independent and is not affiliated with, endorsed by, or
sponsored by YouTube, Google, or OpenAI.
