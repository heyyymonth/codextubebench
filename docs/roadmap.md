# TubeBench Roadmap

## Current

- Freeze the TubeBench identity and source-of-truth docs.
- Preserve and validate the 12 deterministic fixture tasks.
- Preserve and validate the 12 live YouTube task contracts.
- Preserve and validate the 24-task `live_public_video_v0` catalog and its
  aggregate-only pilot reporting boundary.
- Use the failure taxonomy for every new failed or partial Codex trace.
- Keep mock results labeled as pipeline diagnostics.
- Treat the 24-slot live public video pilot as complete and formal, but not as
  a repeated benchmark score.

## Next

1. Finish manual evidence review and paper-safe reporting for the v0 live
   public video pilot.
2. Run the 72-slot retained live-public campaign:
   `24 tasks x 3 seeds`, with no replacement of blocked slots.
3. Run the deterministic experiment set in
   `docs/next_codex_experiments.md`.
4. Add automatic browser/tool-call normalization.
5. Add generic state-restoration scoring.
6. Add primary and contributing failure-category fields to evaluated results.
7. Encode recurring live failures as deterministic fixture variants.
8. Compare instrumented, GUI-native, and transcript-assisted Codex modes.
9. Add complete latency and cost telemetry only after repeated-run capture is
   stable.

## Later

- encoded benchmark-owned audiovisual fixtures;
- stronger browser/OS side-effect auditing;
- multilingual and transcript-missing fixture variants;
- automated isolated-profile Codex execution;
- report generation from repeated, frozen Codex aggregates.
