# Live Public Video Protocol

`live_public_video_v0` is a volatile public-page evaluation lane for
long-form video browsing workflows. It is not a deterministic leaderboard and
must not be pooled with local fixture results.

The v0 catalog is:

- 24 retained task slots;
- public and unauthenticated;
- read-only for public sites;
- dated by `candidate_metadata.verified_at`;
- split across YouTube, MIT OpenCourseWare, C-SPAN, Internet Archive, and
  Library of Congress public-domain film pages.

The first reviewed v0 pilot was run on June 30, 2026. It retained 24 slots,
completed 22, blocked 2, and recorded 0 unsupported claims. This is a formal
dated live-public pilot result, not a deterministic leaderboard and not a
repeated browser-agent benchmark result.

## Scope

The track measures whether an agent can open public video pages, inspect
visible metadata and controls, capture screenshot-backed observations, report
blocked or volatile page states, and produce criterion-level evidence.

V0 public tasks do not authorize playback control, seeking, speed changes,
downloads, login, comments, chat, likes, subscriptions, purchases, ad
interaction, or account mutation. Public write-action tasks require
benchmark-owned fixtures.

## Catalog

The task catalog lives at:

```text
benchmarks/live_public_video_v0/tasks/catalog.json
```

Required task fields are:

```text
task_id
site
url
video_type
task_family
task_prompt
allowed_actions
forbidden_actions
expected_evidence
success_criteria
verification_requirements
volatility_level
candidate_metadata
```

Validation command:

```bash
PYTHONPATH=src python3 -m tubebench.cli validate-live-public-video
```

## Trace Schema

Private attempts use:

```text
schemas/live_public_video_trace.schema.json
```

The trace records observations, screenshot refs, page refs, browser/tool calls,
actions, watched intervals, criteria results, final answer, final verification,
failures, recovery attempts, side effects, metrics, and outcome.

Screenshots and raw traces stay in the lab repository under ignored run paths.
Trace validation rejects raw browser/account artifacts such as cookies,
profiles, credentials, raw DOM, local storage, browser history, and transcript
dumps.

Trace validation command:

```bash
PYTHONPATH=src python3 -m tubebench.cli validate-live-public-video-trace \
  ../youtube-benchmark-lab/runs/live_public_video/codex/<task-id>/<attempt-id>/trace.json
```

## Interpretation

A completed live public video attempt is a dated pilot observation. A blocked
page, changed page, unavailable video, missing transcript, or browser-controller
failure remains in the retained denominator. Do not replace blocked slots.

Only reviewed aggregate, redacted metrics may be promoted into paper artifacts,
and only after a separate evidence review.

The approved v0 paper handoff is aggregate-only. It excludes attempt IDs, raw
paths, screenshots, raw observations, page text, browser profiles, cookies,
tokens, account fields, and transcript dumps.
