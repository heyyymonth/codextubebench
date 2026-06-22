# Archived: Research Plan

## Workstreams

1. Literature and positioning: maintain a primary-source claim ledger and
   refresh it before every public release.
2. Task design: develop L1–L4 templates, capability annotations, and matched
   access-mode variants.
3. Fixtures and harness: build deterministic long timelines, capability gates,
   trace collection, reset, and oracle interfaces.
4. Metrics and evaluators: validate interval, evidence, disturbance, state,
   verification, rubric, and efficiency scoring.
5. Dataset: harden 25–50 seed tasks, then scale to 200–500 instances with a
   target release near 300.
6. Baselines: implement scripted, transcript, screenshot, GUI, instrumented,
   hybrid, frontier-agent, open-source, and human references.
7. Experiments: run matched access and architecture ablations with repeated
   seeds and paired analysis.
8. Safety and governance: enforce local-first execution, restricted raw data,
   aggregate-only publication, and explicit live YouTube policies.
9. Paper preparation: freeze claims only after evaluator validation and
   statistically supported results.

## Task acceptance gate

A task is accepted only when:

- two reviewers agree the instruction is unambiguous;
- media license and checksum are recorded;
- reset succeeds three consecutive times;
- oracle and negative-control trajectories pass;
- relevant spans have independent annotation;
- at least two valid strategies are documented where appropriate;
- forbidden-action detection has positive and negative tests;
- human completion is at least 90%, excluding intentionally adversarial tasks;
- the task runs within declared safety and resource budgets.

## Milestones

- M0: schemas, ten examples, temporal metrics, provenance, and research docs.
- M1: one local fixture and 12 runnable tasks.
- M2: frozen 25–50 task seed and human references.
- M3: repeated baseline and ablation study.
- M4: first aggregate technical report and optional live track.
- M5: 200–500 task scaled benchmark and submission-ready evidence.

## Decision gates

- Do not implement public write tasks.
- Do not pool access modes or live/fixture tracks.
- Do not promote an experimental adapter before telemetry and reset are stable.
- Do not use mock-pipeline results as research claims.
- Do not move raw traces or authenticated captures into the paper repository.
- Do not claim novelty beyond the primary-source evidence in the claim ledger.
