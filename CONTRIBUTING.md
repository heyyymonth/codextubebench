# Contributing to TubeBench

TubeBench accepts focused changes to public benchmark behavior, task contracts,
fixtures, validators, metrics, tests, and documentation. Raw experiments and
private evidence belong in the lab repository; publication-only changes belong
in the paper repository.

## Start with an issue

- Use the **bug report** template for reproducible validator, fixture, scoring,
  workflow, or documentation defects.
- Use the **benchmark proposal** template for new tasks, predicates, evidence
  channels, failure reproductions, or protocol changes.
- Follow [SECURITY.md](SECURITY.md) for evaluator bypass, secret exposure, or
  unintended-write vulnerabilities. Do not disclose sensitive details in a
  public issue.

## Development setup

Requirements: Python 3.11 or newer. The benchmark runtime is standard-library
only.

```bash
git clone https://github.com/heyyymonth/codextubebench.git
cd codextubebench
make check
```

Keep changes scoped. Do not add a third-party dependency without an explicit
architecture decision explaining why the standard library is insufficient.

## Task and evaluator changes

A new task or task revision must provide:

1. an immutable task ID and explicit revision;
2. a user-visible objective with unambiguous target selection;
3. exact success predicates and required evidence;
4. allowed actions, forbidden actions, and protected state;
5. deterministic setup/reset for any write action;
6. declared access modes and evidence channels;
7. a human reference trajectory and step budget when applicable;
8. fixture ownership, license, and publication permission;
9. evaluator tests for every new predicate or side-effect type;
10. safety, privacy, and failure-mode review.

Public live tasks are read-only. Write-action tasks must use benchmark-owned
fixtures. Browser-only, UI-assisted, instrumented, and hybrid results remain
separate.

Schemas and metric definitions are public contracts. Preserve active schema
versions and add compatibility tests when changing a contract. A breaking
removal requires a version change and an explicit migration note.

## Evidence and privacy

Never commit or attach:

- credentials, tokens, cookies, browser profiles, or authorization headers;
- account identifiers, personal browsing state, or unrelated tabs;
- authenticated captures, private page text, or raw live traces;
- screenshots or DOM captures from private runs;
- full third-party transcripts or unlicensed media.

Use synthetic, redacted examples in tests and issues. Raw run artifacts stay
under the private lab repository's ignored `runs/` tree. Only reviewed,
allowlisted aggregates may cross into publication artifacts.

## Pull request checklist

- Add or update tests for behavioral changes.
- Run `make check` from the public repository.
- Run the relevant CLI command or smoke path with output in a temporary
  directory.
- Confirm `git diff --check` passes.
- Confirm `python3 scripts/release_check.py` passes.
- Update README, benchmark-card, protocol, and compatibility text together when
  changing a public surface.
- If a lab or paper consumer is affected, validate those repositories before
  requesting promotion.
- Keep the pull request free of generated runs, caches, credentials, private
  evidence, and unrelated changes.
