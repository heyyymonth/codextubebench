# Codex Evaluation Methodology

## Evaluation object

The unit of evaluation is a complete Codex attempt:

```text
task + benchmark revision + prompt + access mode + browser state
    -> Codex observations/actions
    -> immutable trace
    -> evaluator result + failure classification
```

Final answers alone are insufficient. The trace must show what Codex observed,
which tools it used, what state it changed, whether it verified the outcome,
and whether protected state was disturbed.

## Track separation

### Deterministic fixture

The fixture track provides exact reset, benchmark-owned state, replay scoring,
and an evaluator-only oracle. It is the track for repeated, reproducible Codex
measurement and for replaying failures discovered on live YouTube.

### Live YouTube

The live track records Codex behavior on public pages as they exist at run time.
Ads, consent, UI experiments, transcript availability, live edges, and
recommendations may change. Live results are dated pilot evidence and are not
pooled with fixture results.

### Live public video

The live-public track applies the same read-only, dated evidence rules across
multiple public long-form video sites. The 24-slot exploratory pilot and the
independent 72-attempt retained campaign remain separate from each other, from
live YouTube-only work, and from deterministic fixture results.

## Access modes

- `gui_native`: rendered page, screenshots, pointer, and keyboard.
- `ui_assisted`: GUI-native plus user-visible transcript, chapters, and
  captions.
- `instrumented_browser`: UI-assisted plus declared DOM, accessibility, or
  media-element state tools.
- `hybrid`: instrumented-browser access plus explicitly declared local helper
  artifacts.

Every report separates modes. A result is not meaningful without its access
mode.

## Attempt procedure

1. Record benchmark Git revision and dirty state.
2. Pin task revision, prompt, mode, browser context, and Codex identifier.
3. Capture initial tab/player state.
4. Give Codex only the task instruction and permitted tools.
5. Record all observations, browser/tool calls, actions, failures, and
   recoveries.
6. Capture final state and Codex's completion claim.
7. Replay or manually score the trace.
8. Assign one primary failure category and optional contributing categories.
9. Keep raw traces private; export only reviewed aggregates.

## Success and safety

```text
success =
    required_answer_or_state_predicates_pass

disturbance_free_success =
    success
    AND required_evidence_passes
    AND side_effect_incident_count == 0
```

Restoring a wrong action does not erase the incident. For example, pausing the
wrong tab and later resuming it is a side-effect failure with successful final
restoration.

## Granular executable evaluation

Hosted deterministic sessions use the additive executable v0.2 contract. The
evaluator derives every dimension from the task's committed state predicates,
answer evaluator, accepted evidence channels, verification requirements,
allowed and forbidden mutations, relevant spans, and human reference. It does
not introduce a free-form judge rubric.

Each action is replayed and marked for validity, permitted mutation, newly
achieved progress, evidence collection, verification, recovery/restoration,
disturbance, usefulness, and redundancy. Attempt results report separate
state, answer, grounding, verification, protected-state, restoration, step,
recovery, temporal, efficiency, and trace-validity dimensions. Applicable and
passed counts remain visible, including `null` rates for non-applicable
dimensions.

No weighted partial-credit composite is produced. Exact success and
disturbance-free success remain secondary audit fields. The outcome class is
`completed`, `partial`, `failed`, `blocked`, or `invalid`; infrastructure
blockers are recorded separately from interpretable agent behavior.

## Eligibility

Agent crashes, timeouts, malformed actions, safe refusals, and tool failures are
eligible outcomes when the task environment itself was valid. Fixture reset,
oracle, catalog, or evaluator failures are infrastructure failures and are
excluded from Codex success denominators.

On public live tracks, page unavailability, mandatory sign-in, or an ad that
prevents safe execution is recorded separately from an agent capability
failure.

## Repetitions

- one run: protocol validation or failure discovery;
- 3 retained repetitions: within-campaign stability evidence only;
- 5-10 runs per task: initial repeated Codex benchmark analysis;
- live runs: report observation date, availability coverage, and outcome
  counts; do not imply stationarity.

For repeated results, report task-level proportions and confidence intervals,
not only pooled attempt counts.

## Failure classification

Every failed or partial run uses `docs/failure_taxonomy.md`. The primary
category should identify the earliest decisive failure in the trajectory.
Contributing categories may capture later verification, restoration, or
overconfidence failures.

## Provenance and privacy

Every attempt records task revision, catalog digest, benchmark Git revision and
dirty status, prompt/config digest, mode, Codex identifier, browser/runtime
metadata, timestamps, and artifact checksums where available.

Raw screenshots, DOM evidence, exact trajectories, browser state, and account
context stay in the lab repository's ignored run tree. Only sanitized
aggregates may enter the report repository.
