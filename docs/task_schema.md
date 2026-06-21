# Task Schema

The pilot catalog is a compact executable form of `schemas/task.schema.json`.
Each task declares:

- identity, track, mode, title, and goal;
- risk level;
- canonical initial state;
- exact success predicates;
- explicit allowed and forbidden mutations;
- a reference step count;
- deterministic mock actions used only for harness validation.

Production task revisions must additionally pin fixture, reset, oracle,
instruction, evaluator, and human-reference versions. Instructions must not
leak selectors, IDs, DOM positions, or target tab indices.

The allowed mutation list is an allowlist. Real adapters must reject undeclared
state-changing actions before execution, not merely score them afterward.
