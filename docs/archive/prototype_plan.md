# Archived: First Prototype and 30/60/90-Day Plan

## First working prototype

### Scope

Build one deterministic local YouTube-like site with:

- three 30–45 minute benchmark-authored virtual videos;
- multiple tabs and players;
- seek, playback rate, mute, captions, chapters, and transcript;
- one visual-only event, one unique phrase, and one late correction;
- deterministic reset and privileged oracle state;
- one task-scoped report template.

Implement 12 runnable tasks:

- four L1 controls;
- four L2 localization/evidence tasks;
- two L3 cross-tab tasks;
- two L4 artifact tasks.

### Required pipeline

1. Resolve and validate task, fixture, access policy, and agent config.
2. Record Git revision and dirty state.
3. Reset fixture and capture privileged pre-state.
4. Execute only through the capability-gated session.
5. Record observations, actions, tool calls, watched intervals, channels,
   checkpoints, side effects, and verification.
6. Capture final answer/artifact and post-state.
7. Run independent evaluators.
8. Cleanup and verify reset.
9. Write manifest, trace, result, and checksums.
10. Export a redacted aggregate bundle through the lab.

### Acceptance criteria

- Existing TubeControl CLI and tests remain green.
- All four access modes produce distinct mode-tagged manifests.
- Illegal capability requests are denied and traced.
- Watch metrics derive only from interval evidence.
- Transient disturbances are detected after restoration.
- Fixture reset succeeds three times consecutively.
- Every run records benchmark Git revision and dirty status.
- Mixed-mode summaries fail closed unless explicitly grouped.
- No raw trace enters the paper repository.

## Days 1–30

- Commit and pin the three repository baselines.
- Review and freeze candidate v2 contract semantics.
- Build the first local fixture player and oracle/reset protocol.
- Convert 12 seed contracts into runnable tasks.
- Add attended-interval, repeated-exposure, and transient-disturbance logging.
- Implement scripted and diagnostic baselines.
- Validate aggregate redaction end to end.

Exit criterion: one command produces a versioned trace, result, and safe
aggregate from a clean local fixture run.

## Days 31–60

- Expand to 25–50 validated seed tasks.
- Add screenshot-only, GUI-native, UI-assisted, transcript-only, and
  instrumented baselines.
- Collect at least three human references per task.
- Validate annotation agreement, reset reliability, and evaluator
  false-positive/negative behavior.
- Run a three-seed engineering pilot.
- Freeze the seed release after critical defects are resolved.

Exit criterion: reproducible seed benchmark with mode-separated baseline and
human-reference results.

## Days 61–90

- Run at least five repetitions of benchmark comparisons and matched ablations.
- Conduct structured error analysis.
- Produce the first non-synthetic aggregate release.
- Author 100–150 scale-up candidates.
- Validate the first optional live read-only subset.
- Audit claims, privacy, licenses, and statistical analysis.

Exit criterion: defensible technical report, public seed artifact, and a clear
gate for scaling toward 300 tasks in months four through six.
