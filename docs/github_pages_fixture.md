# GitHub Pages Static Fixture Fallback

This fallback exists only when the Codex in-app browser cannot attach to the
local deterministic fixture. It is a standalone, agent-facing TCE-002 page
that can be served over HTTPS by GitHub Pages.

It is not equivalent to the dynamic fixture:

- supported task: `TCE-002` only;
- supported mode: `gui_native` only;
- no evaluator authority, session API, protected reset, or server-side trace;
- no client-side scoring;
- exported traces are manual/static protocol-validation artifacts.

The initial `task-cockpit` is deliberately no-scroll-first. At supported
browser sizes it keeps the instruction, all three playback states, the single
task action, verification, and status in the initial viewport. After the
playing player is paused, verification becomes available. Selecting it
idempotently submits the blank answer and switches the cockpit to a completed
layout containing the result summary, visible trace textarea, and transfer
controls without requiring page scrolling.

Keyboard operation is available when focus is not already inside a control:

- `P` or Space pauses the sole playing player;
- `V` selects final-state verification and finalizes the trace;
- `C` attempts to copy the visible trace after completion;
- Tab and Enter retain their native meanings.

Keep `CODEXTUBEBENCH_PUBLIC_BASE_URL` reserved for the dynamic fixture contract
documented in `hosted_fixture.md`. Set the eventual static URL separately:

```bash
export CODEXTUBEBENCH_STATIC_FIXTURE_URL="https://heyyymonth.github.io/codextubebench/"
```

## Local preview

From `youtube-benchmark/`:

```bash
python3 -m http.server 8088 --directory docs/static-fixture
```

Open `http://127.0.0.1:8088/`. The page records only its own deterministic UI
actions. After pausing player B and selecting verification, the complete trace
appears in a read-only textarea. This visible text is the primary transfer
path; clipboard and download remain optional conveniences.

Manual ingestion:

```bash
RUN_DIR="../youtube-benchmark-lab/runs/static_fixture/codex/<run-id>"
mkdir -p "$RUN_DIR"
$EDITOR "$RUN_DIR/trace.json"

PYTHONPATH=src python3 -m tubebench.cli score-static-trace \
  --trace "$RUN_DIR/trace.json" \
  --output "$RUN_DIR/result.json"
```

If clipboard or downloads are blocked, choose **Select trace text**, copy the
selected textarea contents with the browser's normal text operation, and paste
them into `trace.json`. Do not upload traces, screenshots, or result files to
Pages.

## GitHub Pages deployment

The public repository is:
`https://github.com/heyyymonth/codextubebench`.
Its expected Pages root is:
`https://heyyymonth.github.io/codextubebench/`.

1. Push the intended clean public revision to `main`.
2. Configure Pages with GitHub Actions as the build source.
3. Manually run **Deploy static CodexTubeBench fixture**.
4. Record the deployed root in `CODEXTUBEBENCH_STATIC_FIXTURE_URL`.
5. Verify the page and deployment metadata over HTTPS before running one
   isolated GUI-native smoke.

The manual workflow deploys only `docs/static-fixture/` and replaces
`deployment-metadata.json` with the exact Git revision and workflow deployment
identifier. It does not read repository secrets.

## Evidence boundary

A static trace may prove that an isolated Codex worker can access and interact
with the deterministic UI over HTTPS. It does not prove dynamic reset/oracle
isolation, instrumented-browser access, or repeated benchmark performance.
Label it `static browser-visible smoke`, keep it private, and do not include it
in campaign aggregates.
