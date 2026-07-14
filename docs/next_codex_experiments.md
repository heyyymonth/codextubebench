# Next Codex Experiments

This document specifies the next experiments; it does not execute them.

## Set A — Deterministic fixture repeated Codex runs

- Tasks: all 12 `TubeControl-Executable-v0` tasks.
- Repetitions: 5 minimum, 10 preferred per task/mode.
- First mode: `instrumented_browser`.
- Second mode: `gui_native` browser-only.
- Fixed inputs: benchmark revision, task revision, Codex identifier, prompt,
  browser build, viewport, and mode policy.
- Report: success, verification, side effects, restoration, timestamp error,
  watch ratio, steps, browser/tool calls, failure categories, task-level
  confidence intervals, and all-run reliability.

Do not begin reporting until the worktree is clean and revisions are pinned.

## Set B — Live YouTube pilot

- Tasks: 10 reviewed public-page tasks.
- Coverage: long-form educational/interview/lecture videos, long music/ambient
  videos, and live streams.
- Safety: signed out, isolated browser, read-only, no ad interaction, no account
  mutation.
- Capture: live trace v0.2, initial/final state, criterion evidence, failures,
  recovery, verification, and restoration.
- Scoring: manual or semiautomatic review followed by sanitized aggregation.
- Report: dated outcome counts and failure categories, not a stable success
  rate.

## Set B2 — Live public video retained campaign

- Starting point: the 24-slot `live_public_video_v0` pilot completed 22 slots
  and blocked 2 on June 30, 2026.
- Next campaign: 24 tasks x 3 retained seeds = 72 attempts.
- Planning contract: `live-public-video-retained-v1` uses fresh retained
  repetition IDs `17`, `29`, and `43`; it does not reuse the pilot seed.
- Trace contract: `live-public-video-trace.v0.2`, with clean revision and
  manifest provenance required for every retained slot.
- Safety: public, unauthenticated, isolated browser, read-only, no downloads,
  no ad interaction, no account mutation, no comments/chat/likes/subscribes.
- Capture: private traces and screenshots under the lab run tree only.
- Report: aggregate-only site, task-family, outcome, failure-stage, evidence,
  screenshot, unsupported-claim, and blocked-rate metrics.
- Retention: blocked slots remain in the denominator and are never retried or
  replaced.
- Claim boundary: dated live-public evidence only; do not call the 72-slot
  campaign a deterministic leaderboard.

## Set C — Failure replay

For each important live failure:

1. identify the earliest decisive failure;
2. classify it with `docs/failure_taxonomy.md`;
3. encode a privacy-safe deterministic fixture variant;
4. add a clean trajectory and a failing trajectory test;
5. rerun Codex on the fixture;
6. compare whether the live failure reproduces.

Prioritize wrong-tab actions, ambiguous player state, missing verification,
unrestored speed/mute/current time, transcript misuse, and pre-roll/live-edge
confusion.

## Set D — Mode comparison

Compare matched semantic tasks under:

1. `instrumented_browser`;
2. `gui_native` browser-only;
3. `ui_assisted` transcript/chapter/caption access.

Measure:

- which tasks require instrumented state;
- whether transcript assistance reduces watching but creates visual-evidence
  failures;
- whether GUI-native mode increases grounding errors;
- whether verification and restoration differ by mode;
- which browser/tool calls Codex depends on.

Do not pool modes into one score.

## Recommended execution order

1. Freeze docs, prompts, catalogs, and schemas.
2. Clean and pin all repository revisions.
3. Run Set A in instrumented mode.
4. Review failures and evaluator coverage.
5. Run Set A in GUI-native mode.
6. Run Set B2 as the next live-public retained campaign.
7. Run Set B only after deterministic capture is stable.
8. Convert important Set B and Set B2 failures through Set C.
9. Run Set D after enough matched traces exist.
