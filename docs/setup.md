# CodexTubeBench Setup

CodexTubeBench is the benchmark name. The Python package and CLI remain
`tubebench` for backward compatibility.

## Local validation

Requirements:

- Python 3.11 or newer.
- GNU Make is optional.

Run:

```bash
make test validate executable-smoke release-check
```

No account, API key, or network access is required for validation and fixture
controls.

## Codex fixture runs

Start the local fixture with:

```bash
PYTHONPATH=src python3 -m tubebench.cli serve-fixture --port 8765
```

Then follow `docs/codex_evaluation_protocol.md`.

## Live YouTube runs

Use an isolated, signed-out browser and follow
`docs/live_youtube_protocol.md`. Never reuse a personal profile or transmit
credentials, cookies, account identifiers, or unrelated browser state.
