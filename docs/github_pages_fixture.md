# GitHub Pages Static Fixture Fallback

This fallback exists only when the Codex in-app browser cannot attach to the
local deterministic fixture. It is a standalone, agent-facing TCE-002 page
that can be served over HTTPS by GitHub Pages.

It is not equivalent to the dynamic fixture:

- supported task: `TCE-002` only;
- supported mode: `gui_native` only;
- no evaluator authority, session API, protected reset, or server-side trace;
- no client-side scoring;
- downloaded traces are manual/static protocol-validation artifacts.

Keep `CODEXTUBEBENCH_PUBLIC_BASE_URL` reserved for the dynamic fixture contract
documented in `hosted_fixture.md`. Set the eventual static URL separately:

```bash
export CODEXTUBEBENCH_STATIC_FIXTURE_URL="https://<owner>.github.io/<repo>/"
```

## Local preview

From `youtube-benchmark/`:

```bash
python3 -m http.server 8088 --directory docs/static-fixture
```

Open `http://127.0.0.1:8088/`. The page records only its own deterministic UI
actions. After submitting the blank state-only answer, download the JSON trace
and move it into the lab's ignored run tree before evaluation.

Re-score privately:

```bash
PYTHONPATH=src python3 -m tubebench.cli score-executable-trace \
  ../youtube-benchmark-lab/runs/deterministic_codex/static/<run-id>/trace.json \
  --output ../youtube-benchmark-lab/runs/deterministic_codex/static/<run-id>/evaluated-trace.json
```

Do not upload the trace, screenshots, or evaluated output to Pages.

## Prepare GitHub Pages

No repository or Pages site is created by this project. After an operator
creates and pushes the public repository:

1. In repository settings, select **Pages** and choose **GitHub Actions** as
   the source.
2. Open **Actions** and manually run **Deploy static CodexTubeBench fixture**.
3. Record the deployment URL in `CODEXTUBEBENCH_STATIC_FIXTURE_URL`.
4. Verify the page over HTTPS before running one isolated GUI-native smoke.

The manual workflow deploys only `docs/static-fixture/` and replaces
`deployment-metadata.json` with the exact Git revision and workflow deployment
identifier. It does not read repository secrets.

## Evidence boundary

A static trace may prove that an isolated Codex worker can access and interact
with the deterministic UI over HTTPS. It does not prove dynamic reset/oracle
isolation, instrumented-browser access, or repeated benchmark performance.
Label it `static fixture protocol-validation smoke`, keep it private, and do
not include it in campaign aggregates.
