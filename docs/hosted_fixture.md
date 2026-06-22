# Hosted HTTPS Deterministic Fixture

The supported remote execution surface is a provider-neutral OCI image that
runs the existing stateful fixture as one ephemeral, single-origin service.
The application serves HTTP inside the container; an approved host must
terminate HTTPS in front of it.

This implementation does not mean a deployment exists. Until an operator
supplies an approved HTTPS origin and evaluator secret, no Codex attempt may be
run and no result aggregate may be created.

## Security and topology

- Run exactly one replica. Sessions are in memory and must not be distributed
  across replicas.
- Route one HTTPS origin to the container's HTTP port. Do not enable CORS.
- Keep `CODEXTUBEBENCH_ORACLE_TOKEN` only in the deployment secret store and
  evaluator shell. Never expose it to the browser, prompt, logs, image, or
  source repository.
- The service applies a one-hour session TTL and a 128-session cap by default.
  Override them only with positive integer
  `CODEXTUBEBENCH_SESSION_TTL_SECONDS` and
  `CODEXTUBEBENCH_MAX_SESSIONS` values.
- Run the container as its packaged non-root user, with a read-only filesystem,
  dropped capabilities, and no persistent volume.
- Disable and remove the deployment after the approved evaluation window.

## Build and push

From `youtube-benchmark/`:

```bash
test -z "$(git status --porcelain)" || {
  echo "refusing to build from a dirty worktree" >&2
  exit 1
}
REVISION="$(git rev-parse HEAD)"
IMAGE="REGISTRY.example/codextubebench-fixture:${REVISION}"
docker build --pull --label "org.opencontainers.image.revision=${REVISION}" \
  --tag "${IMAGE}" .
docker push "${IMAGE}"
```

The build context excludes Git data, runs, builds, profiles, cookies, private
keys, and secret-like files. Hosted health metadata reports a clean deployment
only under this clean-build gate.

## Runtime environment

Create a mode-`0600` environment file outside the repository:

```text
PORT=8080
CODEXTUBEBENCH_ORACLE_TOKEN=<generated evaluator secret>
CODEXTUBEBENCH_PUBLIC_BASE_URL=https://fixture.example
CODEXTUBEBENCH_GIT_REVISION=<exact image Git revision>
CODEXTUBEBENCH_DEPLOYMENT_ID=<host deployment identifier>
CODEXTUBEBENCH_SESSION_TTL_SECONDS=3600
CODEXTUBEBENCH_MAX_SESSIONS=128
```

Provider-neutral container invocation:

```bash
docker run --detach --name codextubebench-fixture \
  --env-file /secure/path/codextubebench-fixture.env \
  --publish 127.0.0.1:8080:8080 \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 128 --memory 512m --cpus 1 \
  "${IMAGE}"
```

Configure the approved host's TLS proxy to forward
`https://fixture.example` to `http://127.0.0.1:8080`. Keep the deployment at
one replica and do not add sticky-session or shared-state assumptions.

Hosted mode binds `0.0.0.0:$PORT` and fails closed unless all four required
`CODEXTUBEBENCH_*` values are present. Its startup JSON and public endpoints
never include the oracle token. Hosted reset, oracle, trace export, and session
deletion require the evaluator's `X-Oracle-Token`; ordinary browser actions and
submission remain agent-facing.

## Health and sanitized catalog

```bash
curl --fail --silent --show-error \
  https://fixture.example/health | python3 -m json.tool

curl --fail --silent --show-error \
  https://fixture.example/api/catalog | python3 -m json.tool
```

`/health` exposes only suite/deployment provenance, fixture version, catalog
digest, and task count. `/api/catalog` exposes only task IDs, revisions, and
supported modes.

## CLI preflight

Load the evaluator token into the operator shell without printing it, then run:

```bash
python3 -m tubebench.cli preflight-fixture \
  --url https://fixture.example \
  --mode instrumented_browser \
  --task TCE-002 \
  --output-dir ../youtube-benchmark-lab/runs/deterministic_codex
```

The command verifies HTTPS/assets, deployment provenance, clean state, catalog
and task compatibility, state mutation/reset, oracle and trace isolation,
authenticated evaluator access, session deletion, and output writability. It
writes `preflight-report.json`, which contains no oracle material.

Loopback HTTP is rejected except in tests that explicitly pass
`--allow-http-loopback-test`. That flag is not valid evidence for a hosted
evaluation.

When validating the OCI image locally, override the container command with
`serve-fixture --hosted --allow-http-loopback-test` and run the CLI with the
same explicit flag. Never use that exception for a remote or reportable run.

## Browser-visible preflight and smoke gate

After the CLI passes, open:

```text
https://fixture.example/?preflight=1&task=TCE-002&mode=instrumented_browser
```

The page must show `Fixture preflight ready`. This mode loads page assets and
sanitized metadata without creating a benchmark session.

Only after both preflights pass may the operator run exactly one TCE-002
instrumented-browser attempt. Store its raw and evaluated traces in the
ignored lab run tree and label it `deterministic fixture smoke attempt`. Do
not export it to the paper or treat it as repeated empirical evidence.

## Teardown

Disable public routing first, then stop and remove the ephemeral service:

```bash
docker stop codextubebench-fixture
docker rm codextubebench-fixture
```

Revoke the evaluator secret and confirm the HTTPS origin no longer serves the
fixture.

## Deferred alternatives

- **Provider-driven runner (Option B):** deferred. It needs provider
  credentials, a new automation adapter, and a separate authority review.
- **Manual ingestion (Option C):** protocol-validation fallback only. A
  manually captured trace may validate the evaluator path but is not a
  repeated benchmark result.
