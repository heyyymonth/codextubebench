# Agent Instructions

- Keep the core dependency-free unless a dependency is justified in an ADR.
- Treat schemas and metric definitions as public compatibility contracts.
- Never add credentials, cookies, browser profiles, account identifiers, or
  authenticated raw page captures.
- Public write-action tasks must use benchmark-owned fixtures.
- Keep browser-only and hybrid results separate.
- Add evaluator tests for every new predicate or side-effect type.
- Run `make test validate` before submitting changes.
