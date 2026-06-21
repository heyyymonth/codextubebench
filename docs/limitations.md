# Limitations

- The current runner is a deterministic state simulator, not a browser agent.
- Final-state side-effect checks do not detect transient disturbances; live
  adapters must add event-level auditing.
- The task catalog has not yet been hardened against real YouTube UI drift.
- No benchmark-owned video corpus, browser reset adapter, or account setup is
  included yet.
- No live model results or human baselines are claimed.
- The literature and product claims motivating this project require a
  primary-source verification pass before paper submission.
- UI experiments, ads, consent state, personalization, regional differences,
  accessibility trees, and network behavior remain future work.
