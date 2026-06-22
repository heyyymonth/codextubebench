# Archived: Baseline Implementation Plan

## Common protocol

Every baseline must use the same task instruction, capability-gated session,
trace writer, reset logic, budgets, and evaluator. A privileged diagnostic
oracle may validate fixtures but cannot be presented as an agent result.

The agent protocol should expose:

- request observation through a declared channel;
- execute a declared browser or workspace action;
- record structured notes without accessing oracle state;
- submit an answer or artifact reference;
- declare completion or inability.

## Implementation order

1. Harden the existing perfect, no-op, reckless, and transient-disturbance
   mocks as evaluator controls.
2. Add a scripted local-fixture browser baseline for L1.
3. Add transcript-only retrieval with timestamp mapping for eligible L2–L4
   tasks.
4. Add screenshot-only VLM interaction.
5. Add GUI-native Playwright interaction without hidden selectors.
6. Add UI-assisted transcript, caption, chapter, description, and search
   adapters.
7. Add instrumented DOM, accessibility, JavaScript, and media-state access with
   complete channel logging.
8. Add planner/executor/verifier and memory/task-graph ablations.
9. Defer optional task-scoped helper adapters until the YouTube browser tracks
   are stable.
10. Add provider-specific frontier and open-source agents in the lab.
11. Collect human trajectories only after tasks, reset, and evaluators freeze.

## Baseline-specific expectations

### Scripted browser

Targets deterministic L1 controls. It establishes whether fixtures and
evaluators are operable and whether a non-reasoning system can exploit stable
selectors. It is not expected to generalize to paraphrased or visual tasks.

### Transcript-only

Receives cue text and timestamps but no frames. It establishes which factual
tasks are text-sufficient and must fail visual-only tasks by design.

### Screenshot-only and GUI-native

These are the cleanest human-interface comparisons. They must not receive DOM
coordinates, hidden labels, raw transcripts, or privileged media time.

### Instrumented browser

This approximates practical browser agents. Every DOM query, accessibility
read, JavaScript expression, and player-state read is logged. Direct platform
APIs remain prohibited.

### Declared hybrid helper

Receives only task-scoped input and output locations. It cannot read repository
fixtures, oracle files, unrelated user files, browser profiles, or shell
secrets. This is a secondary future-work condition, not the core benchmark.

### Human baseline

Collect at least three trajectories per task after stabilization. Record mode,
steps, watched intervals, active time, completion, verification, and observed
side effects. Human references are distributions, not an assumed perfect path.

## Acceptance gates

A baseline adapter is promotable from lab to stable benchmark interfaces when:

- all capability uses and denials are traced;
- no undeclared state change bypasses the action proxy;
- reset succeeds three consecutive times;
- repeated runs produce schema-valid artifacts;
- required telemetry coverage is complete;
- evaluator controls distinguish perfect, noop, reckless, and transient
  behavior;
- no credentials, account identifiers, raw authenticated captures, or private
  paths enter public artifacts.
