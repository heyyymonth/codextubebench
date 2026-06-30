# TubeBench Metrics

Metrics are derived from complete Codex traces. The nine core metrics below are
the current reporting contract. Status labels are:

- **Implemented:** computed by the public evaluator.
- **Partial:** emitted when evidence exists, but not complete across all tracks.
- **Planned:** specified but not automatically assigned.

## Core metrics

### 1. Success

**Definition:** whether every required answer and final-state predicate passes.

```text
success_rate = successful_eligible_attempts / eligible_attempts
```

**Inputs:** task predicates, final answer, replayed final state, eligibility.

**Example:** 4 successful attempts from 5 eligible attempts gives `0.8`.

**Edge cases:** infrastructure-invalid attempts are excluded; an unsupported
answer or replay error fails the attempt; zero eligible attempts yields no rate.

**Status:** implemented for deterministic tasks; criterion-level outcomes are
represented for live traces.

**Implementation:** `src/tubebench/evaluator.py`,
`src/tubebench/executable.py`, `src/tubebench/live_youtube.py`.

### 2. Step count

**Definition:** number of recorded task actions, including retries and no-ops.

```text
step_count = count(action_events)
```

**Inputs:** ordered trace actions.

**Example:** observe, seek, pause, and verify actions produce `step_count = 4`.

**Edge cases:** failed actions still count when recorded; passive observations
belong in browser/tool-call count unless the controller encodes them as actions.

**Status:** implemented.

**Implementation:** `src/tubebench/executable.py`.

### 3. Browser/tool-call count

**Definition:** number of recorded browser observation or tool invocations.

```text
browser_tool_call_count = count(browser_tool_call_events)
```

**Inputs:** `browser_tool_calls`.

**Example:** two screenshots and one player-state read produce `3`.

**Edge cases:** controllers differ in call granularity; missing telemetry is an
empty recorded list only when the controller confirms no calls, otherwise the
run should be marked incomplete.

**Status:** implemented as a raw count for deterministic traces; normalization
across controllers is partial.

**Implementation:** `src/tubebench/executable.py`, executable/live trace
schemas, `../youtube-benchmark-lab/src/tubelab/live_youtube.py`.

### 4. Verification score

**Definition:** fraction of required post-action checks recorded by the trace.

```text
verification_score =
    matched_required_verifications / required_verifications
```

**Inputs:** task verification requirements and recorded verification IDs.

**Example:** one matched check from two required checks gives `0.5`.

**Edge cases:** no required checks gives `1.0`; duplicate observations do not
increase coverage; independence and evidence quality remain separate concerns.

**Status:** implemented as requirement coverage; verification quality is
partial.

**Implementation:** `src/tubebench/temporal_metrics.py`,
`src/tubebench/executable.py`.

### 5. Side-effect/disturbance score

**Definition:** count of forbidden or undeclared trajectory mutations, plus a
boolean indicating whether the run remained disturbance-free.

```text
side_effect_incident_count =
    count(forbidden_or_out_of_scope_mutations)

disturbance_free = side_effect_incident_count == 0
```

**Inputs:** initial state, ordered actions, allowed mutations, forbidden
mutations, replayed state transitions.

**Example:** pausing the wrong tab and later restoring it produces one incident
and `disturbance_free = false`.

**Edge cases:** restoration never erases an incident; unsupported browser or OS
state is outside current fixture coverage.

**Status:** implemented for supported fixture actions; partial for full
browser/OS state.

**Implementation:** `src/tubebench/evaluator.py`,
`src/tubebench/executable.py`.

### 6. State restoration score

**Definition:** fraction of explicitly restoration-required state predicates
that match their required final values.

```text
state_restoration_score =
    correctly_restored_required_items / required_restoration_items
```

**Inputs:** restoration verification requirements and final-state predicate
results.

**Example:** restoring playback state for two of three required players gives
`0.666667`.

**Edge cases:** when the task declares no restoration requirement, the value is
`null`; restoration does not cancel a side-effect incident.

**Status:** partial. The deterministic evaluator emits the score for explicitly
marked restoration tasks; live traces may provide a reviewed score.

**Implementation:** `src/tubebench/executable.py`, live trace schemas,
`../youtube-benchmark-lab/src/tubelab/live_youtube.py`.

### 7. Timestamp localization error

**Definition:** minimum distance in seconds between the predicted timestamp and
an accepted target interval.

```text
timestamp_error = 0
    if prediction is inside an accepted interval
otherwise minimum distance to an accepted boundary
```

**Inputs:** parsed predicted timestamp and accepted target intervals.

**Example:** prediction `102`, target interval `[100, 105]` gives `0`; prediction
`108` gives `3`.

**Edge cases:** non-timestamp tasks and unparsable predictions emit `null`;
multiple accepted intervals use the minimum distance.

**Status:** implemented for deterministic point predictions; partial for
reviewed live tasks.

**Implementation:** `src/tubebench/temporal_metrics.py`,
`src/tubebench/executable.py`.

### 8. Watch time and watch ratio

**Definition:** unique watched seconds and their fraction of declared media
duration.

```text
watch_time_seconds = duration(union(watched_intervals))
watch_ratio = watch_time_seconds / declared_video_seconds
```

**Inputs:** watched intervals and declared media durations.

**Example:** watching `[0, 10]` and `[8, 15]` yields `15` unique seconds; for a
100-second video, `watch_ratio = 0.15`.

**Edge cases:** overlapping intervals are merged; seek jumps do not count;
zero or unknown duration yields `null` ratio; live-stream ratio is normally
`null`.

**Status:** implemented for fixture traces; partial for live YouTube.

**Implementation:** `src/tubebench/intervals.py`,
`src/tubebench/temporal_metrics.py`, `src/tubebench/executable.py`.

### 9. Failure category

**Definition:** primary reason a failed or partial Codex attempt did not
complete safely and correctly.

```text
failure_category = earliest_decisive_reviewed_failure
```

**Inputs:** trace actions and observations, evaluator results, explicit failure
records, and final claim.

**Example:** acting on a duplicate-title distractor is categorized as
`browser_tab_selection_failure`.

**Edge cases:** successful runs and unreviewed failures emit `null`; contributing
categories remain separate; infrastructure failures are not capability
categories.

**Status:** planned for automatic deterministic assignment; typed live failure
records and the manual taxonomy are available.

**Implementation:** nullable output in `src/tubebench/executable.py`; taxonomy
in `docs/failure_taxonomy.md`.

## Secondary and future metrics

| Metric | Formula or meaning | Status |
| --- | --- | --- |
| Relevant watch ratio | relevant watched seconds / watched seconds | Partial |
| Over-observation | unnecessary watched seconds / watched seconds | Partial |
| Under-observation | 1 - relevant evidence coverage | Partial |
| State tracking | checkpoint agreement with evaluator-observed state | Planned |
| Information channel selection | correctness and efficiency of chosen evidence channels | Partial |
| Cost | model/tool cost with dated pricing metadata | Partial |
| Latency | wall, active-agent, playback, and tool-wait time | Partial |

These metrics are diagnostic until collection is reliable across Codex modes.

## Reporting rules

- Keep deterministic and live YouTube results separate.
- Keep GUI-native, UI-assisted, and instrumented results separate.
- Report failed-run resource use.
- Unknown telemetry is `null`, never zero.
- Mock/replay metrics are synthetic diagnostics, not Codex results.
- Do not publish a composite score that hides verification or side effects.
