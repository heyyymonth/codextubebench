# Setup

## Mock/replay pilot

Requirements:

- Python 3.11 or newer.
- GNU Make is optional.

Run:

```bash
make test validate smoke
```

No account, browser, API key, or network access is required.

## Future verified browser mode

Use a dedicated browser profile and benchmark-owned fixtures. Never reuse a
personal browser profile. Signed-in runs require benchmark-owned OAuth users;
credentials must remain in an OS keychain or secret manager and must never be
passed to the model, command line, trace, or repository.

Write-capable adapters must fail closed unless the task declares the exact
mutation, the target resource is allowlisted, and the operator explicitly
enables writes.
