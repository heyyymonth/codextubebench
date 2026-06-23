# Deterministic Fixture Protocol

`TubeControl-Executable-v0` is the reproducible proxy track for
Codex-on-YouTube failures. The legacy catalog ID is preserved for compatibility.

## What it tests

The 12 tasks cover:

1. identifying the playing media instance;
2. pausing only the intended video;
3. pausing all playing videos;
4. restoring original playback states;
5. seeking to a timestamp;
6. changing playback speed;
7. muting and verifying;
8. using chapters or transcript to locate a segment;
9. answering a timestamp-localized question;
10. locating a visual-only event;
11. comparing two long-form sources;
12. detecting and reporting a restored side effect.

These are deterministic proxies for failures seen or expected on YouTube:
wrong-tab actions, ambiguous state, missing verification, timestamp errors,
channel misuse, and incomplete restoration.

## Determinism boundary

The fixture uses a virtual media timeline. Actions update an in-memory state
machine, and the evaluator independently replays the trace from the initial
state. The browser page does not receive success predicates, accepted answers,
relevant spans, or the oracle token.

The fixture is not evidence that Codex can handle encoded video, ads, real
YouTube UI drift, or live streams.

## Run controls

```bash
make validate
make executable-smoke
PYTHONPATH=src python3 -m tubebench.cli serve-fixture --port 8765
```

Open:

```text
http://127.0.0.1:8765/?task=TCE-002&mode=gui_native&agent=codex
```

Follow `docs/codex_evaluation_protocol.md` for a real Codex attempt.

## Score an exported trace

```bash
PYTHONPATH=src python3 -m tubebench.cli score-executable-trace \
  ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/trace.json \
  --output ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/evaluated-trace.json
```

For the static TCE-002 GitHub Pages fallback, use the manual ingestion and
`score-static-trace` procedure in `docs/github_pages_fixture.md`.

## Current scoring

Implemented:

- success;
- step count;
- trajectory side effects;
- verification coverage;
- timestamp error;
- watch ratio;
- weighted fixture efficiency.

Partial:

- browser/tool-call normalization;
- relevant/over/under-observation;
- information-channel selection;
- cost and latency;
- generic state-restoration ratio;
- automatic Codex failure category.

## Promotion rule

A live YouTube failure should become a fixture case when its decisive behavior
can be represented without copying private or authenticated page data. Add a
negative test proving the evaluator distinguishes the failure from a clean
trajectory.
