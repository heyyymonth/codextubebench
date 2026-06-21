# TubeBench

TubeBench is a research benchmark for operational YouTube browser use. It
focuses on temporal media state, transcript navigation, cross-tab targeting,
workflow completion, and completing requested actions without disturbing
unrelated state.

This repository is the clean public artifact. Raw authenticated traces,
benchmark-account details, exploratory notebooks, and unstable experiments
belong in the separate lab repository.

## Status

The current release is a research scaffold with:

- a 24-task TubeControl pilot catalog;
- versioned task, trace, result, and rubric schemas;
- deterministic predicate and side-effect evaluators;
- a mock/replay runner for evaluator and pipeline validation;
- prompts/configuration examples for future browser agents;
- methodology, safety, setup, and benchmark-card documentation.

It does **not** claim live-browser benchmark results yet.

## Quick start

Python 3.11+ is sufficient; the core has no third-party dependencies.

```bash
make test
make validate
make smoke
```

The smoke run writes results and traces under `runs/smoke/`.

## CLI

```bash
PYTHONPATH=src python3 -m tubebench.cli validate
PYTHONPATH=src python3 -m tubebench.cli run \
  --agent mock-perfect \
  --seed 1 \
  --output runs/example
PYTHONPATH=src python3 -m tubebench.cli summarize \
  runs/example/results.jsonl
```

## Repository map

- `benchmarks/tubecontrol/tasks/catalog.json`: 24-task pilot.
- `schemas/`: machine-readable contracts.
- `src/tubebench/`: loader, evaluator, runner, trace, and CLI.
- `prompts/`: reusable browser-agent prompts.
- `examples/`: task, trace, and result examples.
- `docs/`: setup, methodology, safety, limitations, and contribution rules.
- `skills/`: reusable authoring and analysis instructions.

## Research tracks

- **TubeControl:** short-horizon deterministic operations.
- **TubeWorkflow:** medium-horizon YouTube workflows, initially schema-only.
- **TubeStudio:** controlled creator-side tasks, initially schema-only.

Verified and live modes are reported separately. Browser-only and hybrid
tool-assisted agents must never share one leaderboard.

Paper URL: to be added when the paper has a stable public location.
