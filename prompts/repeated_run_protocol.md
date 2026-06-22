# Repeated Codex run protocol

Use this operator checklist for every repeated CodexTubeBench attempt.

1. Pin benchmark revision, task revision, prompt revision, mode, Codex
   identifier, browser build, and viewport.
2. Start from a fresh fixture reset or isolated browser context.
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

Use 5-10 repetitions per task for initial repeated results. Keep access modes
separate and randomize task order with a recorded seed.
