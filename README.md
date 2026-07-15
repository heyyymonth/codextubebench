# TubeBench

TubeBench is a dependency-free benchmark and evaluation harness for studying
how browser-use agents handle long-form video tasks. It captures observations,
actions, evidence, verification, and side effects so that completion and
failure can be audited at the trajectory level.

- [Published paper](https://heyyymonth.github.io/codextubebench/paper/)
- [TCE-002 static fixture](https://heyyymonth.github.io/codextubebench/)
- [Benchmark card](BENCHMARK_CARD.md)

TubeBench is the public benchmark name. The Python package remains `tubebench`,
and active catalog IDs, schema versions, deployed fixture IDs, environment
variables, and JavaScript globals remain compatibility contracts.

## Current evidence

| Evidence lane | Current status | Interpretation |
| --- | --- | --- |
| Deterministic mock/replay | Four frozen diagnostic conditions over the 24-task `tubecontrol` catalog | Evaluator and aggregation checks, not agent performance |
| Deterministic fixture | 12 runnable `TubeControl-Executable-v0` tasks, additive granular v0.2 tracing, and retained TCE-002 protocol-validation traces | Reproducible task design and protocol evidence; no repeated benchmark result yet |
| Live public video pilot | 24 retained slots: 22 completed and 2 blocked | Dated exploratory aggregate; blocked slots remain in the denominator |
| Retained live-public campaign | 72 fresh attempts: 63 completed and 9 partial | One repeated dated browser/model configuration, not a leaderboard or general competence claim |
| Live YouTube-only track | Catalog, schemas, validator, and private analysis path exist | No approved public or paper aggregate |

The 72-attempt campaign ran on July 14, 2026 with three repetitions. Each
repetition completed 21 of 24 tasks; the same three timestamp-localization tasks
were partial in every repetition. The pilot and campaign are independent and
are never pooled.

## Repository contents

| Path | Purpose |
| --- | --- |
| `benchmarks/tubecontrol/` | Synthetic diagnostic task catalog used by the frozen paper controls |
| `benchmarks/tubecontrol_executable_v0/` | Deterministic browser fixture tasks and replay scoring contracts |
| `benchmarks/live_youtube_v0/` | Planned read-only YouTube pilot contracts |
| `benchmarks/live_public_video_v0/` | Public-page task catalog used by the reviewed pilot and retained campaign |
| `src/tubebench/` | CLI, validators, runners, fixture server, scoring, and temporal metrics |
| `fixtures/longform_player/` | Benchmark-owned deterministic browser surface used by the executable track |
| `docs/static-fixture/` | TCE-002-only GitHub Pages fallback and manual trace handoff |
| `docs/paper/` | Published PDF plus provenance required by the Pages deployment |
| `schemas/`, `prompts/`, `tests/` | Active contracts, operator prompts, and release gates |

Raw traces, screenshots, browser state, and mutable experiment configuration do
not belong here. They stay in the private lab repository; the paper receives
only reviewed aggregate, redacted results.

## Quick start

Requirements: Python 3.11 or newer. The runtime uses only the Python standard
library.

```bash
make check
```

`make check` runs the unit tests, validates every retained catalog, scans the
release tree, and verifies the published paper artifact. The optional fixture
control smoke is:

```bash
make executable-smoke
```

It runs scripted and no-op controls, not Codex or another deployed agent.

## Run one deterministic task

Record the exact benchmark revision and validate the checkout:

```bash
git status --short --branch
git rev-parse HEAD
make test validate
```

Start the local fixture:

```bash
PYTHONPATH=src python3 -m tubebench.cli serve-fixture --port 8765
```

Open a task such as:

```text
http://127.0.0.1:8765/?task=TCE-002&mode=gui_native&agent=codex
```

Follow the [single-run protocol](docs/codex_evaluation_protocol.md). Store the
exported raw trace under the private lab repository, then replay-score it:

```bash
PYTHONPATH=src python3 -m tubebench.cli score-executable-trace \
  ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/trace.json \
  --output ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/evaluated-trace.json
```

Browsers that cannot reach loopback may use the gated
[hosted HTTPS fixture](docs/hosted_fixture.md). The
[GitHub Pages fallback](docs/github_pages_fixture.md) is limited to TCE-002 and
uses `score-static-trace`; it is not a replacement for the dynamic fixture.

Hosted sessions emit `tubecontrol-executable-trace.v0.2`, which adds stable
event identifiers, evaluator-only state snapshots, deterministic step flags,
failure/recovery records, outcome classes, and a dimension vector. The
original v0.1 trace and result contracts remain supported for local scripted
runs and the static TCE-002 fixture. Granular results intentionally contain no
single partial-credit composite.

## Experimental tracks

- [Deterministic fixture](docs/deterministic_fixture.md): exact reset,
  benchmark-owned state, replay scoring, protected-state checks, and
  evaluator-only oracle access.
- [Live YouTube](docs/live_youtube_protocol.md): volatile, signed-out,
  read-only public YouTube tasks. No current aggregate is approved.
- [Live public video](docs/live_public_video_protocol.md): dated read-only tasks
  across YouTube, MIT OpenCourseWare, C-SPAN, Internet Archive, and Library of
  Congress pages.

Fixture, live-YouTube, exploratory live-public, and retained-campaign results
must remain separate. A completed live attempt is not automatically a
deterministic benchmark result.

## Method and contracts

- [Methodology](docs/methodology.md)
- [Metrics and implementation status](docs/metrics.md)
- [Task taxonomy](docs/task_taxonomy.md)
- [Failure taxonomy](docs/failure_taxonomy.md)
- [Next experiments](docs/next_codex_experiments.md)
- [Limitations](docs/limitations.md)

Every reported attempt records the benchmark revision and dirty state, task and
prompt revisions, access mode, browser/runtime metadata, and evidence status.
Live tasks are read-only: no login, likes, subscriptions, comments, saves,
donations, chat, downloads, purchases, ad interaction, or account mutation.

## Compatibility in 0.2.0

Version `0.2.0` removes the unused `validate-longform` command, abandoned
`longform_seed` catalog and validators, orphan long-form/rubric schemas,
unreferenced configuration examples, and superseded planning documents. Active
diagnostic, live-YouTube, live-public, and static trace interfaces are
unchanged. The executable track adds v0.2 trace/result contracts and the
`export-fixture-session` command while retaining v0.1 compatibility.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a bug fix, benchmark
task, protocol change, or evaluator predicate. Never attach credentials,
cookies, profiles, authenticated captures, account identifiers, private traces,
or full third-party transcripts to a public issue or pull request.

Security-sensitive reports follow [SECURITY.md](SECURITY.md). TubeBench is
independent and is not affiliated with, endorsed by, or sponsored by YouTube,
Google, or OpenAI. The repository is licensed under the [MIT License](LICENSE).
