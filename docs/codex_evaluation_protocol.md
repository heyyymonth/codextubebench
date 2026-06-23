# Single-Run Codex Evaluation Protocol

This protocol runs Codex on one deterministic CodexTubeBench task, captures the
browser interaction as a trace, and scores it with the public evaluator. It is
manual/semiautomatic; the repository does not yet launch repeated Codex runs
through a provider API. The output label is `Codex protocol validation`, not a
benchmark result.

## 1. Validate the benchmark revision

From `youtube-benchmark/`:

```bash
git status --short --branch
git rev-parse HEAD
make test validate
```

Record the Git revision and dirty state. Dirty runs are valid development
traces but must not be promoted as release results.

## 2. Select and preflight the fixture surface

For a browser that can reach loopback, start the local fixture:

```bash
PYTHONPATH=src python3 -m tubebench.cli serve-fixture \
  --host 127.0.0.1 \
  --port 8765
```

The first output line contains:

```json
{"base_url":"http://127.0.0.1:8765","oracle_token":"..."}
```

Keep the oracle token outside the agent prompt and browser page. It is evaluator
authority.

For a browser that cannot reach loopback, follow `docs/hosted_fixture.md`.
Hosted execution requires this sequence:

1. deploy one ephemeral fixture replica behind an approved HTTPS origin;
2. run `tubebench preflight-fixture`;
3. open `?preflight=1&task=TCE-002&mode=instrumented_browser` in the actual
   in-app browser and verify `Fixture preflight ready`;
4. run exactly one TCE-002 instrumented-browser smoke attempt;
5. export and re-score its private trace;
6. review that trace before planning or starting the 60-attempt campaign.

If no approved HTTPS URL and evaluator secret exist, stop after documentation
and deployment preparation. Do not create a session, smoke trace, or aggregate.
Runtime access failures are infrastructure blockers, never Codex failures.

## 3. Open one task

Example GUI-native task:

```text
http://127.0.0.1:8765/?task=TCE-002&mode=gui_native&agent=codex-manual
```

Give Codex only:

- the task instruction shown on the page;
- the declared mode;
- browser interaction tools appropriate to that mode;
- the requirement to submit the final answer through the page.
- the focused prompt in `prompts/codex_executable_task.md`.

Do not provide the catalog, expected answer, success predicates, relevant spans,
scripted baseline, oracle token, or evaluator output.

## 4. Allowed tools by mode

- `gui_native`: rendered page, screenshots, pointer, and keyboard only.
- `ui_assisted`: GUI-native plus visible transcript and chapter controls.
- `instrumented_browser`: UI-assisted plus the page's visible instrumented
  player-state panel or declared DOM/player-state tools.
- `hybrid`: instrumented browser plus explicitly declared local artifacts.

If Codex uses a forbidden channel, record the run as policy-invalid rather than
silently removing the event.

## 5. Capture the run

The fixture records:

- state-changing actions;
- browser action calls received by the fixture;
- watched intervals;
- transcript cues and chapters selected;
- DOM/player-state reads in instrumented mode;
- verification declarations;
- final answer.

If the browser controller produces screenshots, save them under the private lab
run directory and add relative paths to `screenshots` before scoring. Do not put
raw screenshots or authenticated captures in the paper repository.

After Codex submits, copy the session id displayed in the page header and export
the evaluated trace from a separate evaluator shell:

```bash
curl -sS \
  -H "X-Oracle-Token: <token printed by the server>" \
  "http://127.0.0.1:8765/api/sessions/<session-id>/trace" \
  > ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/trace.json
```

The output must stay in the lab's ignored `runs/` tree until it is reviewed and
aggregated.

## 6. Validate and score

The exported endpoint already returns a replay-scored trace. Re-score it from
the file to verify reproducibility:

```bash
PYTHONPATH=src python3 -m tubebench.cli score-executable-trace \
  ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/trace.json \
  --output ../youtube-benchmark-lab/runs/deterministic_codex/<task-id>/<run-id>/evaluated-trace.json
```

The static Pages fallback has no evaluator endpoint. Its visible textarea must
be ingested and scored with `score-static-trace`; follow
`docs/github_pages_fixture.md`.

Confirm that the command's result agrees with:

- `passed`;
- `final_oracle_state`;
- `side_effects`;
- `metrics.success`;
- `metrics.verification_score`;
- `metrics.timestamp_localization_error_seconds`;
- `metrics.watch_ratio`;
- `metrics.weighted_efficiency`;
- `errors`.

## 7. Interpretation

A single manual or hosted smoke trace establishes only that the protocol can capture and
score a real Codex-controlled interaction. It is not a benchmark score.
Population-level claims require a clean pinned revision, repeated runs, fixed
mode and prompt, task-complete coverage, environment metadata, and aggregate
export through the lab repository.

For repeated runs, use `prompts/repeated_run_protocol.md` and
`docs/next_codex_experiments.md`.
