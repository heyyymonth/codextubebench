# Long-Form Browser-Use Experiment Framework

This document audits the current TubeBench workspace and defines the next
measurement framework for long-form browser-use agents. It is intentionally
additive: it does not approve raw traces, promote lab data, or convert protocol
validation into benchmark-level performance evidence.

## Executive Summary

TubeBench already has the right high-level shape for publishable applied AI
evaluation:

- `youtube-benchmark/` owns public tasks, fixtures, schemas, prompts,
  evaluator semantics, examples, and release checks.
- `youtube-benchmark-lab/` owns raw and mutable experiment work, private run
  traces, unstable analysis, and aggregate-only export tooling.
- `youtube-benchmark-paper/` owns the manuscript, claims ledger, frozen
  aggregate data, generated tables, and generated figures.

The current empirical evidence is bounded. The repository supports deterministic
fixture validation, live YouTube task contracts, live v0.2 trace analysis, and
paper generation, but there is no repeated browser-agent benchmark result and no
approved live YouTube aggregate. Static TCE-002 campaigns are protocol
validation only: they demonstrate trace handoff, readiness checks, and runtime
blocker accounting, not general Codex performance on YouTube.

The next credible research step is not another one-off pilot. It is a staged
framework that captures every attempt as a task, prompt, mode, browser surface,
trace, criterion-level result, failure annotation, and aggregate row. The
benchmark should report where the trajectory failed, not only whether the final
answer looked correct.

## Current-State Audit

### Workspace Map

| Area | Important paths | Role | Status |
| --- | --- | --- | --- |
| Umbrella | `README.md`, `WORKSPACE.md`, `workspace.lock.json`, `Makefile` | Repo boundary contract and cross-repo validation | Present and consistent with the three-repo split |
| Public benchmark | `benchmarks/`, `schemas/`, `prompts/`, `src/tubebench/`, `fixtures/`, `docs/`, `tests/` | Stable benchmark behavior and public contracts | Substantial and testable |
| Private lab | `configs/`, `runs/`, `analysis/`, `src/tubelab/`, `scripts/`, `docs/` | Mutable experiments, raw traces, analysis, export | Raw runs ignored; export path exists |
| Paper repo | `paper/`, `latex/`, `bibliography/claims-ledger.csv`, `data/`, `tables/`, `figures/`, `scripts/` | Manuscript, claim tracking, frozen aggregates | Claims are bounded to methodology and protocol validation |

### Existing Experiments and Assets

| Asset | Location | What it measures | Evidence status |
| --- | --- | --- | --- |
| Compatibility mock suite | `benchmarks/tubecontrol/tasks/catalog.json` | Legacy evaluator and paper-pipeline diagnostics | Synthetic only |
| Long-form seed contracts | `benchmarks/longform_seed/tasks/catalog.json` | Schema-level task ideas | Not executable fixture evidence |
| TubeControl executable fixture | `benchmarks/tubecontrol_executable_v0/tasks/catalog.json` | 12 deterministic media-control and evidence tasks | Runnable through scripted/noop/random controls |
| Live YouTube catalog | `benchmarks/live_youtube_v0/tasks/catalog.json` | 12 public-page live task contracts | Planned volatile protocol; no approved YouTube-only publication aggregate |
| Live public video catalog | `benchmarks/live_public_video_v0/tasks/catalog.json` | 24 public-page tasks across YouTube, MIT OCW, C-SPAN, Internet Archive, and LOC | One reviewed 24-slot dated pilot; aggregate-only paper handoff |
| Static GitHub Pages fallback | `docs/static-fixture/` and deployed page | TCE-002-only browser-visible trace handoff | Protocol validation only |
| Static TCE-002 campaigns | `youtube-benchmark-lab/analysis/deterministic_codex/run_status.json` | Readiness, trace capture, retained blockers | Protocol validation only |
| Synthetic paper aggregate | `youtube-benchmark-paper/data/frozen-results/latest/aggregate-results.json` | Paper generation and diagnostic controls | Synthetic diagnostic controls |

The strongest implemented deterministic task surface is
`TubeControl-Executable-v0`, with these task families:

- active-player identification and state-preserving inspection;
- pausing one or multiple players without disturbing protected players;
- temporary mutation and restoration;
- timestamp seek and verification;
- playback speed and mute changes;
- transcript and chapter lookup;
- timestamp-localized transcript answering;
- visual-only event localization;
- cross-source comparison;
- restored side-effect detection.

The live catalog covers long-form lectures, long music or ambient videos, and
live streams. Its value is external-validity discovery: transcript availability,
ads, YouTube UI drift, live edges, DVR windows, and player-state volatility.
Live results must stay dated and separate from deterministic fixture results.

### Prompts and Agents

Prompts are currently organized under `prompts/`:

- `browser_only.md`
- `codex_executable_task.md`
- `live_youtube_codex_task.md`
- `repeated_run_protocol.md`

Implemented public baselines are deterministic controls, not model results:

- compatibility mock agents: `mock-perfect`, `mock-reckless`,
  `mock-transient`, `mock-noop`;
- executable controls: `scripted`, `noop`, `random`, `transcript-only`.

The lab reserves configurations for `codex-in-app-browser`, planner-executor,
skill-augmented, browser-only, hybrid, and live YouTube pilots, but the checked
in aggregates are not repeated autonomous Codex benchmark evidence.

### Metrics Already Specified

The public metric contract covers:

- exact success;
- step count;
- browser/tool-call count;
- verification score;
- side-effect or disturbance score;
- state restoration score;
- timestamp localization error;
- watch time and watch ratio;
- failure category.

The key implementation gap is not that metrics are absent. It is that repeated
Codex traces are not yet available across all deterministic tasks and modes, so
many metrics remain unpopulated, partial, or manually reviewed.

### Reusable Entry Points

| Entry point | Repository | Purpose |
| --- | --- | --- |
| `python3 -m tubebench.cli validate` | public | Validate compatibility task catalog |
| `python3 -m tubebench.cli validate-executable` | public | Validate TubeControl executable tasks |
| `python3 -m tubebench.cli validate-live-youtube` | public | Validate live YouTube task contracts |
| `python3 -m tubebench.cli run-executable` | public | Run scripted/noop/random executable controls |
| `python3 -m tubebench.cli score-executable-trace` | public | Replay and score one executable trace |
| `python3 -m tubebench.cli score-static-trace` | public | Score the TCE-002 static fallback trace |
| `python3 -m tubebench.cli serve-fixture` | public | Serve deterministic local fixture |
| `scripts/check_static_fixture_ready.py` | lab | Precheck the static fallback |
| `scripts/analyze_live_youtube.py` | lab | Analyze reviewed private live traces |
| `scripts/export_paper_data.py` | lab | Export aggregate-only paper data |
| `scripts/import_lab_release.py` | paper | Convert lab release into paper aggregate schema |
| `scripts/generate_artifacts.py` | paper | Validate aggregate and regenerate tables/figures |

### Paper Claims

The paper currently supports methodology claims, not capability claims. The
claims ledger correctly blocks repeated success-rate, model-comparison, and
general competence claims until repeated reviewed aggregates exist.

Supported now:

- TubeBench defines a task and trace protocol for browser-media interaction.
- Final-answer-only scoring hides trajectory failures.
- Diagnostic controls validate scorer and publication-pipeline behavior.
- Retained static blockers identify runtime and trace-handoff failure layers.

Weak or blocked now:

- Any general claim about Codex or another browser agent being good or bad at
  long-form YouTube tasks.
- Any repeated task-level success rate or confidence interval.
- Any prompt, mode, or model comparison.
- Any live YouTube success rate.
- Any claim that static TCE-002 covers the full benchmark.

## Cleanup Proposal

The current repo split should be preserved. The cleanup should focus on making
experiment intent, evidence labels, schemas, and validation gates harder to
misread.

### Keep

- Public benchmark contracts in `youtube-benchmark/`.
- Raw or unstable experiments under ignored `youtube-benchmark-lab/runs/`.
- Aggregate-only paper handoff.
- Claims ledger as the release gate for paper statements.
- Synthetic/mock data labels.
- Separation between deterministic fixture, static protocol validation, live
  public-page pilots, and repeated benchmark results.

### Add or Clarify

| Need | Proposed location | Rationale |
| --- | --- | --- |
| Experiment framework overview | `youtube-benchmark/docs/longform_experiment_framework.md` | Public design contract for the next measurement phase |
| Repeated-run aggregate v2 proposal | This document first; schema later | Avoid prematurely freezing a public schema before traces exist |
| Prompt comparison matrix | `youtube-benchmark-lab/configs/` after authorization | Prompt experiments are mutable lab work |
| Reviewed deterministic aggregate | `youtube-benchmark-lab/analysis/deterministic_codex/` then aggregate-only paper export | Raw evidence stays private |
| Paper claim update | `youtube-benchmark-paper/bibliography/claims-ledger.csv` | Only after reviewed aggregate data exists |

### Cleanup Candidates

- The paper aggregate schema is sufficient for synthetic controls but too narrow
  for future criterion-level browser-agent results. It will need an extension
  for eligibility, blocked counts, failure stages, confidence intervals,
  task-level results, prompt/config digests, and evidence-coverage metrics.
- `hybrid_enterprise` in docs and `hybrid` in executable schemas are retained
  compatibility names. Future reports should use one display label per result.
- The live analyzer can produce a private aggregate, but its output is not a
  paper-approved schema. Do not export it until there is an explicit live
  evidence review.
- Static protocol-validation aggregates remain useful but should not be mixed
  with the dynamic 60-attempt campaign.

## Proposed Repo Structure

The existing structure already approximates the desired layout. The target
state should be interpreted as ownership, not as a request to move files now.

| Desired concept | Current owner | Current or target paths |
| --- | --- | --- |
| Tasks | public | `benchmarks/*/tasks/catalog.json` |
| Prompts | public for reusable prompts; lab for experimental variants | `prompts/`, future `youtube-benchmark-lab/configs/prompts/` |
| Configs | public for baseline modes; lab for mutable conditions | `configs/`, `youtube-benchmark-lab/configs/` |
| Source | public and lab separately | `src/tubebench/`, `src/tubelab/` |
| Runs | lab only | `youtube-benchmark-lab/runs/` |
| Results | lab analysis first; paper only aggregate/frozen | `analysis/`, `data/releases/`, `data/frozen-results/` |
| Reports | lab private reports and paper public reports | `analysis/*/report.md`, `paper/`, `latex/` |
| Docs | public methodology and private operations | `docs/` in each repository |
| Scripts | repo-local automation | `scripts/` in each repository |

## Experiment Tracks

Each track below should be implemented as lab config first. Only after repeated
review should an aggregate cross into the paper repo.

| Track | Goal | Task set | Prompt/input | Environment | Success criteria | Step-level metrics | Failure modes | Reproducibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Deterministic repeated baseline | Establish first real benchmark result | All 12 TCE tasks | Current `codex_executable_task.md` or frozen equivalent | Hosted HTTPS deterministic fixture, pinned revision | Exact success, DFS, required evidence, no protected-state disturbance | plan quality, navigation, actions, verification, browser/tool calls, watch ratio | wrong target, missed verification, side effect, trace failure, runtime | 5-10 repetitions per task/mode |
| B. Prompt structure ablation | Measure prompt sensitivity | All 12 TCE tasks or a balanced 6-task slice | minimal, structured, stepwise/replanning prompts | Same fixture and browser surface | Matched task-level deltas with confidence intervals | plan completeness, recovery, overconfidence, unsupported claims | task misunderstanding, brittle recovery, over-planning | Same seeds/order per prompt |
| C. Task length scaling | Test degradation with horizon length | short state tasks, medium temporal tasks, long compare/visual tasks | One frozen structured prompt | Deterministic fixture | Success by length bucket plus resource use | actions, tool calls, watched seconds, evidence coverage | time budget, over-observation, stale evidence | Fixed budgets per bucket |
| D. Evidence channel comparison | Compare GUI, transcript, and instrumented access | TCE-008 to TCE-011 plus live contracts after approval | Same task prompt, mode-specific tool policy | `gui_native`, `ui_assisted`, `instrumented_browser` | Correct answer with allowed evidence | channel selection, evidence precision/recall, verification score | transcript misuse, visual under-observation, DOM overreliance | Do not pool modes |
| E. Recovery and replanning | Test recovery from controlled mistakes | TCE tasks with injected distractors or transient failures | baseline vs explicit replanning prompt | Deterministic fixture variants | Recovery succeeds without hiding incident | recovery attempt count, recovered failure rate, final restoration | hidden side effects, overconfident finalization | Injected failure schedule pinned |
| F. Static vs live transfer | Discover product-specific failures | Live LYT tasks and deterministic replay candidates | `live_youtube_codex_task.md` | Isolated signed-out browser; read-only live pages | Dated criterion outcomes, no unsafe actions | availability, criterion score, failure stage, recovery | ads, transcript unavailable, live edge, UI drift | Live is pilot only; convert failures to fixture |
| G. Scripted/browserless controls | Calibrate task difficulty and scoring | TCE tasks and selected answer-only variants | Programmatic controls | No autonomous browser agent | Ceiling/floor references, not model claims | oracle access separated from agent view | evaluator bug, task ambiguity | Public controls must stay diagnostic |

## Step-Level Measurement Framework

Every attempt should be scored through the same lifecycle. Storing the final
answer alone is insufficient.

| Stage | Question | Required evidence | Metrics |
| --- | --- | --- | --- |
| Task understanding | Did the agent restate the right goal, target, and constraints? | plan or first action aligned with task | task-understanding pass/fail, first-decisive-error stage |
| Planning | Did the agent choose a reasonable route within budget? | plan steps or observable strategy | plan completeness, predicted channel selection |
| Navigation | Did it reach the right page/tab/player/source? | tab/player/source observations | navigation success, irrelevant-source count |
| Observation | Did it inspect the right content and state? | screenshots, DOM/player reads, transcript/chapter cues, watched intervals | evidence precision, evidence recall, watch ratio |
| Extraction | Did it extract the right facts, timestamp, or state? | linked observation IDs and values | criterion-level evidence coverage, timestamp error |
| Action | Did it mutate only permitted state? | action events and state snapshots | action success, side-effect incident count |
| Recovery | Did it recover from a dead end or mistake? | failure and recovery records | recoverable failure count, recovered failure count, recovery rate |
| Verification | Did it check the requested final state or answer? | verification events linked to criteria | verification score, unsupported-claim rate |
| Synthesis | Did the final answer satisfy the user intent without overclaiming? | final answer linked to evidence | final quality score, hallucination rate |
| Auditability | Can the run be replayed and attributed? | schema-valid trace, provenance, checksums | trace validity, provenance completeness |

Core rates:

```text
task_completion_rate = completed_eligible_attempts / eligible_attempts
disturbance_free_success_rate = success_with_required_evidence_and_no_incidents / eligible_attempts
recovery_rate = recovered_recoverable_failures / recoverable_failures
unsupported_claim_rate = final_claims_without_linked_evidence / final_claims
navigation_efficiency = minimum_required_source_steps / actual_source_steps
evidence_precision = relevant_evidence_observations / all_evidence_observations
evidence_recall = required_criteria_with_evidence / required_criteria
```

Unknown telemetry is `null`, never zero.

## Task and Result Schema Proposal

The existing executable and live schemas should remain valid. A future v2
aggregate should preserve their per-attempt detail in reviewed aggregate form.

### Task Definition

```yaml
schema_version: tubebench.task.v2
task_id: TCE-010
task_revision: 1
track: deterministic_fixture
family: temporal_visual_localization
length_bucket: long
environment:
  surface: hosted_https_fixture
  allowed_modes: [gui_native]
  required_viewport: 390x600
prompt_contract:
  prompt_id: structured-stepwise-v1
  prompt_digest: sha256:...
objective:
  user_instruction: "Report when the red checksum mismatch banner first appears."
  expected_output_type: timestamp
evidence_requirements:
  required_channels: [visual]
  forbidden_shortcuts: [transcript_only]
scoring:
  criteria:
    - criterion_id: timestamp_in_interval
      required: true
      weight: 0.5
    - criterion_id: visual_reinspection
      required: true
      weight: 0.3
    - criterion_id: no_protected_side_effects
      required: true
      weight: 0.2
reproducibility:
  benchmark_git_revision: "<sha>"
  catalog_digest: "<sha256>"
  fixture_revision: "<sha>"
```

### Prompt Definition

```yaml
schema_version: tubebench.prompt.v1
prompt_id: structured-stepwise-v1
scope: deterministic_fixture
variant_class: stepwise_replanning
allowed_tools: [screenshot, keyboard, pointer, dom_player_state]
instructions_digest: sha256:...
budget:
  max_actions: 30
  max_wall_time_seconds: 600
reporting_requirements:
  - cite_observation_ids
  - state_uncertainty
  - verify_final_state
```

### Attempt Manifest

```yaml
schema_version: tubebench.attempt-manifest.v1
run_id: "20260630T000000Z-TCE-010-codex-001"
experiment_id: deterministic-repeated-v1
task_id: TCE-010
task_revision: 1
agent_id: codex-in-app-browser
mode: gui_native
prompt_id: structured-stepwise-v1
seed: 1
benchmark_git_revision: "<sha>"
benchmark_git_dirty: false
environment:
  surface: hosted_https_fixture
  browser: codex_in_app_browser
  viewport: 390x600
  account_state: signed_out_or_fixture_owned
artifacts:
  raw_trace: runs/deterministic_codex/TCE-010/.../trace.json
  evaluated_trace: runs/deterministic_codex/TCE-010/.../evaluated-trace.json
```

### Attempt Result

```yaml
schema_version: tubebench.attempt-result.v1
run_id: "20260630T000000Z-TCE-010-codex-001"
eligible: true
outcome: partial
exact_success: false
disturbance_free_success: false
criterion_score: 0.55
criteria_results:
  - criterion_id: timestamp_in_interval
    status: partial
    score: 0.5
    evidence_observation_ids: [obs-5, obs-6]
metrics:
  step_count: 14
  browser_tool_call_count: 9
  verification_score: 0.5
  timestamp_error_seconds: 7
  watch_ratio: 0.01
  side_effect_incident_count: 0
failures:
  primary_failure_category: timestamp_localization_failure
  first_decisive_stage: extraction
  contributing_categories: [weak_verification]
```

### Aggregate Result

```yaml
schema_version: tubebench.aggregate.v2
release:
  id: deterministic-repeated-v1-reviewed
  date: 2026-06-30
  benchmark_revision: "<sha>"
  synthetic: false
  evidence_label: repeated_browser_agent_benchmark_result
groupings:
  - agent_id
  - prompt_id
  - mode
  - task_family
summary:
  attempted: 120
  eligible: 118
  completed: 73
  partial: 29
  failed: 16
  blocked: 2
  exact_success_rate: 0.62
  disturbance_free_success_rate: 0.54
  mean_criterion_score: 0.71
  mean_verification_score: 0.66
  unsupported_claim_rate: 0.18
failure_breakdown:
  grounding: 12
  verification: 9
  runtime: 2
confidence:
  method: bootstrap_by_task
  intervals:
    exact_success_rate: [0.50, 0.72]
```

## Failure Taxonomy

Use `docs/failure_taxonomy.md` as the canonical public taxonomy. For deeper
experiments, annotate both a stage and a category:

| Stage | Typical categories |
| --- | --- |
| Availability | candidate unavailable, ad blocked, sign-in required, live stream unavailable |
| Planning | task understanding failure, unsafe plan, missing verification plan |
| Navigation | wrong tab, wrong source, lost page, irrelevant page |
| Perception | visible UI missed, player state misread, transcript affordance misread |
| Grounding | wrong player/control/content region, coordinate miss |
| Extraction | wrong timestamp, wrong fact, incomplete source comparison |
| Action | wrong mutation, forbidden mutation, failed seek, wrong rate/mute |
| Verification | missing check, weak evidence, unsupported final claim |
| Restoration | temporary state not restored, collateral state left changed |
| Runtime | browser/controller failure, trace capture failure, evaluator failure |
| Safety/privacy | account mutation, ad interaction, raw/private artifact capture |

The primary category should be the earliest decisive failure. Later issues such
as weak verification or overconfident finalization should be contributing
categories unless they are the first decisive error.

## Paper Claim Alignment

| Paper claim type | Current support | Action before strengthening |
| --- | --- | --- |
| Methodology: path matters | Supported by task protocol, trace schemas, and static protocol validation | Keep as core contribution |
| Diagnostic controls validate scorer and paper pipeline | Supported by frozen synthetic aggregate | Keep labeled synthetic/control |
| Static blockers expose runtime failure layers | Supported by lab run status and paper text | Keep as protocol validation |
| Deterministic fixture task coverage | Design-supported by 12 TCE tasks | Do not imply full empirical coverage until repeated runs exist |
| Codex performance on TubeBench | Blocked | Run repeated deterministic campaign and reviewed aggregates |
| Prompt/mode/model comparison | Blocked | Matched repeated runs with frozen prompts and modes |
| Live YouTube capability estimate | Blocked | Reviewed dated live pilot only; never pool with fixture results |
| Live public video pilot estimate | Supported with bounds | Formal dated one-seed pilot only; not a repeated benchmark score |
| Enterprise-production implications | Weak unless framed as evaluation requirements | Tie to traceability, evidence, recovery, and side-effect accounting |

Paper tables and figures needed for a stronger version:

- task taxonomy table with deterministic/live coverage;
- attempt lifecycle diagram with trace artifacts;
- repeated deterministic result table by task family, mode, and prompt;
- failure-stage heatmap;
- evidence channel precision/recall table;
- verification vs final-answer success table;
- static/live transfer table showing which live failures became fixture tasks;
- claim ledger appendix mapping every numeric claim to aggregate evidence.

## Implementation Roadmap

### Phase 0: Understand Current State

Files to inspect:

- `youtube-benchmark/README.md`
- `youtube-benchmark/BENCHMARK_CARD.md`
- `youtube-benchmark/docs/*`
- `youtube-benchmark-lab/README.md`
- `youtube-benchmark-lab/analysis/deterministic_codex/run_status.json`
- `youtube-benchmark-paper/paper/manuscript.md`
- `youtube-benchmark-paper/latex/main.tex`
- `youtube-benchmark-paper/bibliography/claims-ledger.csv`

Expected output: repo map, evidence status, blocker list, claim support map.

Validation:

```bash
make status
```

Risks: stale docs, unapproved private traces, accidental overclaiming.

### Phase 1: Repo Cleanup

Files to modify:

- public docs only, unless a specific lab or paper claim needs correction.

Expected output: source-of-truth docs that clearly separate diagnostic,
protocol-validation, live pilot, and repeated benchmark evidence.

Validation:

```bash
make -C youtube-benchmark test validate release-check
```

Risks: freezing premature schemas or moving raw data across boundaries.

### Phase 2: Task and Prompt Schema

Files to create or extend:

- public schema proposal after review: `schemas/attempt_manifest.schema.json`
- public schema proposal after review: `schemas/prompt.schema.json`
- lab prompt configs: `youtube-benchmark-lab/configs/prompts/*.json`

Expected output: versioned task, prompt, mode, and attempt contracts.

Validation:

```bash
make -C youtube-benchmark validate
make -C youtube-benchmark test
```

Risks: breaking compatibility with existing TCE and LYT schemas.

### Phase 3: Experiment Runner

Files to modify:

- lab runner scripts, not public benchmark code, unless a stable CLI surface is
  needed.
- public CLI only for fixture-owned scoring or validation contracts.

Expected output: repeated deterministic campaign runner that records task order,
seeds, prompt digest, browser metadata, and no-overwrite run directories.

Validation:

```bash
make -C youtube-benchmark-lab test validate
```

Risks: running without a reviewed HTTPS execution surface, missing evaluator
secret, or silently retrying blocked slots.

### Phase 4: Evaluation Harness

Files to modify:

- `src/tubebench/executable.py`
- `src/tubebench/temporal_metrics.py`
- `docs/metrics.md`
- evaluator tests for every new metric or failure label.

Expected output: criterion-level deterministic results, failure categories,
unsupported-claim tracking, and restoration metrics.

Validation:

```bash
make -C youtube-benchmark test validate
```

Risks: automatic failure labels can be misleading without trace evidence links.

### Phase 5: Report Generation

Files to modify:

- `youtube-benchmark-lab/src/tubelab/analysis.py`
- `youtube-benchmark-lab/src/tubelab/export.py`
- `youtube-benchmark-paper/data/schema/aggregate-results.schema.json`
- `youtube-benchmark-paper/scripts/generate_artifacts.py`

Expected output: aggregate v2 with eligible/blocked/partial counts, confidence
intervals, task-level rows, evidence coverage, and failure-stage breakdown.

Validation:

```bash
make -C youtube-benchmark-lab test validate
make -C youtube-benchmark-paper check DATA=data/frozen-results/latest/aggregate-results.json
```

Risks: paper schema drift, accidental export of raw identifiers, and synthetic
controls being displayed as model results.

### Phase 6: Paper Alignment

Files to modify:

- `youtube-benchmark-paper/bibliography/claims-ledger.csv`
- `youtube-benchmark-paper/paper/manuscript.md`
- `youtube-benchmark-paper/latex/main.tex`

Expected output: claims-ledger-backed paper sections, tables, and limitations
that match available evidence.

Validation:

```bash
make -C youtube-benchmark-paper check
```

Risks: overclaiming live results, missing denominator language, or reporting
pooled scores across modes.

### Phase 7: Extended Experiments

Files to create:

- lab configs for prompt ablations, mode comparisons, recovery injection, and
  reviewed live pilots.
- deterministic fixture variants for reproduced live failures.

Expected output: publishable repeated deterministic result plus separate dated
live pilot observations.

Validation:

```bash
make -C youtube-benchmark test validate release-check
make -C youtube-benchmark-lab test validate check-secrets
make -C youtube-benchmark-paper check DATA=data/frozen-results/latest/aggregate-results.json
```

Risks: insufficient repetitions, no task-level confidence intervals, live-page
drift, and hidden manual intervention.

## Immediate Next Code Changes

The safe first pass is documentation and schema planning only:

1. Keep this framework document in the public benchmark docs.
2. Link it from `README.md` under source-of-truth docs.
3. Do not change raw runs, checked-in aggregates, paper claims, or schemas until
   the next repeated-run design is reviewed.

The next implementation PR should add a lab-side repeated-run manifest and
prompt-config validator. That should happen in `youtube-benchmark-lab/` because
the prompt matrix and run orchestration are experimental until a stable public
contract is proven.
