# TubeBench Setup

TubeBench is the benchmark name. The Python package and CLI remain
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

For local development, start the fixture with:

```bash
PYTHONPATH=src python3 -m tubebench.cli serve-fixture --port 8765
```

Then follow `docs/codex_evaluation_protocol.md`.

For an in-app browser or other environment that cannot reach loopback, use the
provider-neutral OCI deployment in `docs/hosted_fixture.md`. Do not run a
Codex attempt until its HTTPS CLI preflight and browser-visible
`?preflight=1` check both pass.

If the in-app browser cannot attach to loopback and no dynamic HTTPS deployment
is available, prepare the limited GitHub Pages fallback in
`docs/github_pages_fixture.md`. Keep its URL in
`CODEXTUBEBENCH_STATIC_FIXTURE_URL`; it does not satisfy the dynamic fixture
contract.

## Live YouTube runs

Use an isolated, signed-out browser and follow
`docs/live_youtube_protocol.md`. Never reuse a personal profile or transmit
credentials, cookies, account identifiers, or unrelated browser state.
