# Live YouTube Protocol

`live_youtube_v0` specifies how a future approved run may measure dated Codex
behavior on real public YouTube pages. It is a failure-discovery and transfer
protocol, not a deterministic leaderboard.

No live result is currently approved or published. Private ignored traces are
not evidence for active documentation or paper claims until they pass a
separate provenance, privacy, and claims review.

## Safety boundary

- use an isolated, signed-out browser;
- no likes, dislikes, subscriptions, comments, saves, donations, chat,
  downloads, sign-in, or account mutation;
- do not interact with ads;
- exclude private, paid, age-restricted, or login-required content;
- preserve unrelated tabs and restore temporary player changes;
- stop on unsafe ambiguity instead of bypassing it.

Raw screenshots and traces stay under the lab repository's ignored
`runs/live_youtube/` tree.

## Task coverage

The public catalog contains 12 contracts across:

- long-form educational, interview, lecture, or technical videos;
- long music and ambient videos;
- live streams and moving DVR windows;
- timestamp localization and evidence selection;
- player-state inspection, temporary changes, and restoration.

URLs and page metadata may drift. Availability is checked at run time.

## Run procedure

1. Record benchmark revision, dirty state, task revision, prompt, mode, Codex
   identifier, browser context, and observation time.
2. Capture initial tab and player state.
3. Execute the task using `prompts/live_youtube_codex_task.md`.
4. Record every observation, browser/tool call, action, failure, recovery, and
   verification.
5. Capture final state and any restoration attempt.
6. Validate the trace against the current schema.
7. Assign a primary category from `docs/failure_taxonomy.md`.
8. Run lab aggregation only after manual trace review.

## Trace revisions

- `live-youtube-trace.v0.1`: legacy task-level pilot traces.
- `live-youtube-trace.v0.2`: typed observations/actions, criterion outcomes,
  state snapshots, failure records, recoveries, and non-binary outcomes.

Use v0.2 for new work. Preserve v0.1 as immutable historical evidence.

## Interpretation

After approval, use the label `live YouTube pilot result` and report:

- attempted, eligible, completed, partial, failed, and blocked counts;
- availability coverage;
- mode distribution;
- verification and side-effect outcomes;
- restoration outcomes;
- failure categories;
- deterministic fixture candidates.

Do not report a one-pass completion fraction as a stable Codex capability
estimate. Do not pool live results with fixture results.

## Current status

The protocol, schemas, catalog, validator, and private analysis tooling exist.
No live aggregate is approved for the paper or public benchmark. Do not infer a
result from ignored private files.
