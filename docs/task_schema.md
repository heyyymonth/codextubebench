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

## Long-form contract

`schemas/longform_task.schema.json` is a separate public contract. It does not
replace or reinterpret the TubeControl v1 schema. It adds:

- L1-L4 tier and category;
- controlled fixture or live-extension environment;
- eligible access modes and per-mode channel policy;
- pinned media metadata and checksums;
- relevant spans, accepted timestamp spans, and state predicates;
- allowed/forbidden actions and protected state;
- verification obligations;
- human-reference resources and task budgets;
- write risk and cleanup policy.

The access-mode axis is separate from environment stability. GUI-native,
UI-assisted, instrumented-browser, and declared hybrid results must remain
separate. `hybrid_enterprise` is retained only as the compatibility schema
identifier.
