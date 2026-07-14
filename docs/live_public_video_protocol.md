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

The completed independent campaign uses the additive
`live-public-video-trace.v0.2` contract. It predeclares 72 fresh retained
slots (`24 tasks x 3 repetitions`) and records a campaign/manifest digest,
clean benchmark and lab revisions, prompt/catalog/config digests, and runtime
metadata in every trace. The original v0.1 pilot contract remains valid and is
not migrated or pooled into the campaign.

The retained-v1 campaign ran on July 14, 2026 and reconciled all 72 reviewed
attempts: 63 completed, 9 partial, and none failed, blocked, or became invalid.
Seeds `17`, `29`, and `43` each produced 21 completed and 3 partial attempts.
The same three timestamp-localization tasks were partial in every repetition;
the other 21 tasks completed in all three. Evidence and screenshot coverage
were both 1.0, with zero unsupported claims and zero side-effect incidents.
This is a repeated dated live-public result for one browser/model configuration,
not a deterministic leaderboard, cross-agent comparison, or general competence
claim.

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

The retained-v1 campaign uses:

```text
schemas/live_public_video_trace_v0.2.schema.json
```

The trace records observations, screenshot refs, page refs, browser/tool calls,
actions, watched intervals, criteria results, final answer, final verification,
failures, recovery attempts, side effects, metrics, and outcome.

Screenshots and raw traces stay in the lab repository under ignored run paths.
Trace validation rejects raw browser/account artifacts such as cookies,
profiles, credentials, raw DOM, local storage, browser history, and transcript
dumps.

For v0.2, a browser-controller or capture failure after a slot starts may
retain an empty screenshot/observation set only when the outcome is explicitly
`blocked` or `invalid` with a matching runtime/capture failure. This preserves
the failed slot without fabricating evidence.

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

The approved retained-v1 handoff applies the same exclusion boundary and adds
only aggregate repetition, site, task-family, task-stability, outcome,
criterion, failure-type, and failure-stage summaries. The original pilot is
not pooled into its denominator.
