# Repeated Codex run protocol

Use this operator checklist for every repeated CodexTubeBench attempt.

1. Pin benchmark revision, task revision, prompt revision, mode, Codex
   identifier, browser build, and viewport.
2. For a hosted surface, require a passing CLI preflight and browser-visible
   `?preflight=1` check before any attempt. Start from a fresh fixture session
   or isolated browser context.
3. Capture initial tab/player state.
4. Give Codex exactly one task and the mode-appropriate prompt.
5. Record every observation, browser/tool call, action, error, and recovery.
6. Capture Codex's final claim and final browser/player state.
7. Export and validate the trace.
8. Score the attempt without editing raw events.
9. Assign a primary failure category and optional contributing categories.
10. Store raw artifacts in the lab's ignored run directory.
11. Do not overwrite an existing run ID.
12. Record exclusions and infrastructure failures before aggregation.

Before the first campaign, run exactly one TCE-002 instrumented-browser smoke
attempt, export and re-score it privately, and review the capture path. Do not
count that smoke as repeated evidence. If no approved HTTPS URL and evaluator
secret exist, run no attempt and create no aggregate.

Use 5-10 repetitions per task for initial repeated results. Keep access modes
separate and randomize task order with a recorded seed.
