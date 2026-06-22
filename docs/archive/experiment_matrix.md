# Archived: Experiment Matrix

## Baseline conditions

| Condition | Access | Eligible tiers | Purpose |
| --- | --- | --- | --- |
| Diagnostic oracle | Privileged fixture state | L1 | Evaluator upper bound; never a leaderboard agent |
| Scripted browser | Fixed rules through declared UI actions | L1 | Automation floor |
| Transcript-only | Transcript text, no visual playback | L2–L4 subset | Transcript sufficiency and visual blind spots |
| Screenshot-only VLM | Screenshots and pointer/keyboard | GUI-native | Pure visual baseline |
| GUI-native browser agent | Rendered media and browser actions | L1–L3 | Primary browser-only baseline |
| UI-assisted agent | User-visible transcript/captions/chapters | L1–L4 | Normal power-user browser condition |
| Instrumented agent | DOM, accessibility, JavaScript, player state | L1–L3 | Practical tool-assisted condition |
| Planner/executor/verifier | Same access as paired baseline | L2–L4 | Architecture/scaffold comparison |
| Declared hybrid helper | Browser plus explicitly scoped helper tools | L4 subset | Secondary future-work condition |
| Human reference | Mode-matched access | All | Efficiency and ambiguity calibration |

Provider-specific Codex, Claude, Gemini, Agent S2, UI-TARS, BrowserGym, and
other adapters belong in the lab repository. Model availability and
configuration must be dated and pinned when experiments run.

## Primary ablations

Use the same model, semantic task, fixture revision, browser build, and task
ordering:

| Ablation | Primary outcomes |
| --- | --- |
| Transcript on vs off | Success, visual-only failures, watched seconds |
| Screenshot vs screenshot + accessibility | Grounding, steps, latency |
| DOM/player state on vs off | L1 accuracy, disturbance, verification |
| Verification loop on vs off | Disturbance-free success, recovery, latency |
| Memory/task graph on vs history only | L3/L4 state tracking and completion |
| Watch budget on vs off | Observation efficiency and under-observation |
| Disturbance guard on vs off | Side effects and recovery behavior |
| Human-reference hints on vs off | Assisted upper bound; not main ranking |

## Repetition protocol

- Smoke/infrastructure checks: one run.
- Engineering pilot: three seeds.
- Reported baseline comparisons: at least five repetitions.
- Leaderboard-quality stochastic systems: report all-run reliability in
  addition to average success.

## Analysis

- Use paired task-level differences for matched ablations.
- Report cluster-bootstrap confidence intervals by semantic task.
- Correct multiple hypothesis tests within each declared family.
- Publish effect sizes, not only p-values.
- Never pool GUI-native, UI-assisted, instrumented, hybrid, fixture, and live
  results into one ranking.

## Initial prototype matrix

Run the ten current seed examples first as contract tests. The first actual
browser pilot should use 12 runnable fixture tasks:

- four L1 control/state tasks;
- four L2 localization/evidence tasks;
- two L3 cross-tab tasks;
- two L4 YouTube evidence-artifact tasks.

Each eligible task should run under every supported access mode with:

- scripted baseline;
- one model-based browser baseline;
- the same baseline plus explicit verification.
