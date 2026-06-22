from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .executable import (
    SUITE_ID,
    benchmark_provenance,
    catalog_digest,
    load_executable_catalog,
)

REPORT_SCHEMA_VERSION = "codextubebench.fixture-preflight.v0.1"
REPORT_FILENAME = "preflight-report.json"


@dataclass
class Response:
    status: int
    body: bytes
    headers: dict[str, str]
    final_url: str

    def json(self) -> Any:
        return json.loads(self.body)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _origin(value: str) -> tuple[str, str, int | None]:
    parsed = urlparse(value)
    return parsed.scheme, parsed.hostname or "", parsed.port


def _is_loopback_http(value: str) -> bool:
    parsed = urlparse(value)
    return (
        parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        and not parsed.username
        and not parsed.password
    )


def normalize_fixture_url(
    value: str,
    *,
    allow_http_loopback_test: bool,
) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme != "https" and not (
        allow_http_loopback_test and _is_loopback_http(normalized)
    ):
        raise ValueError(
            "fixture URL must use HTTPS; loopback HTTP requires "
            "--allow-http-loopback-test"
        )
    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("fixture URL must be a credential-free origin URL")
    return normalized


def _request(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    oracle_token: str | None = None,
    timeout: float = 10.0,
) -> Response:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if oracle_token is not None:
        headers["X-Oracle-Token"] = oracle_token
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as result:
            return Response(
                status=result.status,
                body=result.read(),
                headers={key.lower(): value for key, value in result.headers.items()},
                final_url=result.geturl(),
            )
    except HTTPError as error:
        return Response(
            status=error.code,
            body=error.read(),
            headers={key.lower(): value for key, value in error.headers.items()},
            final_url=error.geturl(),
        )
    except URLError as error:
        raise RuntimeError(f"fixture request failed: {error.reason}") from error


def _check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    detail: str,
) -> bool:
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


def _write_report(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / REPORT_FILENAME
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)


def _state_changing_action(task: dict[str, Any]) -> dict[str, Any]:
    for action in task["scripted_run"]["actions"]:
        if action.get("type") not in {"observe", "verify"}:
            return action
    raise ValueError(
        f"{task['id']} has no scripted state-changing action for reset preflight"
    )


def preflight_fixture(
    *,
    url: str,
    mode: str,
    task_id: str,
    output_dir: Path,
    oracle_token_env: str = "CODEXTUBEBENCH_ORACLE_TOKEN",
    expected_revision: str | None = None,
    allow_http_loopback_test: bool = False,
    timeout: float = 10.0,
) -> tuple[dict[str, Any], bool]:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "checked_at": _utc_now(),
        "target_url": url.strip().rstrip("/"),
        "task_id": task_id,
        "mode": mode,
        "status": "failed",
        "checks": checks,
        "errors": errors,
    }

    try:
        base_url = normalize_fixture_url(
            url,
            allow_http_loopback_test=allow_http_loopback_test,
        )
        report["target_url"] = base_url
        _check(checks, "url_policy", True, "fixture origin satisfies URL policy")
    except ValueError as error:
        errors.append(str(error))
        _check(checks, "url_policy", False, str(error))
        try:
            _write_report(output_dir, report)
        except OSError:
            pass
        return report, False

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output_dir, delete=True) as handle:
            handle.write(b"preflight")
            handle.flush()
        _check(
            checks,
            "output_directory",
            True,
            "trace output directory is writable",
        )
    except OSError as error:
        message = f"trace output directory is not writable: {error}"
        errors.append(message)
        _check(checks, "output_directory", False, message)

    tasks = load_executable_catalog()
    task = next((row for row in tasks if row["id"] == task_id), None)
    if task is None:
        message = f"task {task_id} is not present in the local executable catalog"
        errors.append(message)
        _check(checks, "local_task", False, message)
    elif mode not in task["supported_modes"]:
        message = f"task {task_id} does not support mode {mode}"
        errors.append(message)
        _check(checks, "local_task", False, message)
    else:
        _check(
            checks,
            "local_task",
            True,
            f"{task_id} revision {task['revision']} supports {mode}",
        )

    local_revision, _ = benchmark_provenance()
    expected_revision = expected_revision or local_revision
    expected = {
        "suite": SUITE_ID,
        "catalog_digest": catalog_digest(tasks),
        "benchmark_git_revision": expected_revision,
        "task_revision": None if task is None else task["revision"],
    }
    report["expected"] = expected

    oracle_token = os.environ.get(oracle_token_env, "")
    if oracle_token:
        _check(
            checks,
            "oracle_token",
            True,
            f"evaluator token loaded from {oracle_token_env}",
        )
    else:
        message = f"evaluator token environment variable {oracle_token_env} is missing"
        errors.append(message)
        _check(checks, "oracle_token", False, message)

    session_id: str | None = None
    cleanup_verified = False
    try:
        query = urlencode({"preflight": "1", "task": task_id, "mode": mode})
        page = _request(f"{base_url}/?{query}", timeout=timeout)
        assets_ok = (
            page.status == 200
            and _origin(page.final_url) == _origin(base_url)
            and b"preflight-panel" in page.body
        )
        for asset, marker in (
            ("app.js", b"Fixture preflight ready"),
            ("styles.css", b":root"),
        ):
            response = _request(f"{base_url}/{asset}", timeout=timeout)
            assets_ok = (
                assets_ok
                and response.status == 200
                and _origin(response.final_url) == _origin(base_url)
                and marker in response.body
            )
        if not _check(
            checks,
            "page_assets",
            assets_ok,
            "preflight page and same-origin assets are reachable",
        ):
            errors.append("fixture page assets are missing or crossed origins")

        health_response = _request(f"{base_url}/health", timeout=timeout)
        health = health_response.json() if health_response.status == 200 else {}
        report["observed_health"] = health
        health_ok = (
            health_response.status == 200
            and health.get("status") == "ok"
            and health.get("suite") == expected["suite"]
            and health.get("catalog_digest") == expected["catalog_digest"]
            and health.get("benchmark_git_revision")
            == expected["benchmark_git_revision"]
            and health.get("benchmark_git_dirty") is False
            and isinstance(health.get("fixture_version"), str)
            and bool(health.get("fixture_version"))
            and isinstance(health.get("deployment_id"), str)
            and bool(health.get("deployment_id"))
            and health.get("task_count") == len(tasks)
        )
        if not _check(
            checks,
            "deployment_metadata",
            health_ok,
            "health metadata matches the local suite, catalog, revision, and clean state",
        ):
            errors.append(
                "deployment metadata mismatch; verify image revision, catalog, and clean deployment"
            )

        catalog_response = _request(f"{base_url}/api/catalog", timeout=timeout)
        catalog = catalog_response.json() if catalog_response.status == 200 else {}
        rows = catalog.get("tasks", []) if isinstance(catalog, dict) else []
        remote_task = next(
            (row for row in rows if isinstance(row, dict) and row.get("id") == task_id),
            None,
        )
        catalog_ok = (
            catalog_response.status == 200
            and remote_task is not None
            and task is not None
            and remote_task.get("revision") == task["revision"]
            and mode in remote_task.get("supported_modes", [])
        )
        if not _check(
            checks,
            "task_and_mode",
            catalog_ok,
            f"hosted catalog exposes {task_id} revision and {mode} support",
        ):
            errors.append("hosted catalog does not match the requested task and mode")

        prerequisites_ok = all(
            check["passed"]
            for check in checks
            if check["name"]
            in {
                "url_policy",
                "output_directory",
                "local_task",
                "oracle_token",
                "page_assets",
                "deployment_metadata",
                "task_and_mode",
            }
        )
        if prerequisites_ok and task is not None:
            create = _request(
                f"{base_url}/api/sessions",
                method="POST",
                body={"task_id": task_id, "mode": mode, "agent": "fixture-preflight"},
                timeout=timeout,
            )
            created = create.json() if create.status == 201 else {}
            session_id = created.get("session_id")
            created_ok = create.status == 201 and isinstance(session_id, str)
            if not _check(
                checks,
                "session_creation",
                created_ok,
                "temporary benchmark session created",
            ):
                errors.append("temporary fixture session could not be created")

            if created_ok and session_id is not None:
                session_url = f"{base_url}/api/sessions/{session_id}"
                unauthorized_oracle = _request(
                    f"{session_url}/oracle", timeout=timeout
                )
                unauthorized_trace = _request(
                    f"{session_url}/trace", timeout=timeout
                )
                auth_isolation_ok = (
                    unauthorized_oracle.status == 403
                    and unauthorized_trace.status == 403
                )
                if not _check(
                    checks,
                    "unauthenticated_isolation",
                    auth_isolation_ok,
                    "unauthenticated oracle and trace requests return 403",
                ):
                    errors.append("oracle or trace endpoint is exposed without evaluator auth")

                initial_response = _request(
                    f"{session_url}/oracle",
                    oracle_token=oracle_token,
                    timeout=timeout,
                )
                initial_state = (
                    initial_response.json() if initial_response.status == 200 else None
                )
                auth_oracle_ok = (
                    initial_response.status == 200
                    and isinstance(initial_state, dict)
                )
                if not _check(
                    checks,
                    "authenticated_oracle",
                    auth_oracle_ok,
                    "evaluator-authenticated oracle access succeeded",
                ):
                    errors.append("evaluator-authenticated oracle access failed")

                action = _state_changing_action(task)
                action_response = _request(
                    f"{session_url}/actions",
                    method="POST",
                    body=action,
                    timeout=timeout,
                )
                changed_response = _request(
                    f"{session_url}/oracle",
                    oracle_token=oracle_token,
                    timeout=timeout,
                )
                changed_state = (
                    changed_response.json() if changed_response.status == 200 else None
                )
                changed_ok = (
                    action_response.status == 200
                    and changed_response.status == 200
                    and changed_state != initial_state
                )
                if not _check(
                    checks,
                    "state_change",
                    changed_ok,
                    f"scripted {action.get('type')} action changed fixture state",
                ):
                    errors.append("state-changing preflight action did not change oracle state")

                reset_response = _request(
                    f"{session_url}/reset",
                    method="POST",
                    body={},
                    timeout=timeout,
                )
                reset_oracle_response = _request(
                    f"{session_url}/oracle",
                    oracle_token=oracle_token,
                    timeout=timeout,
                )
                reset_state = (
                    reset_oracle_response.json()
                    if reset_oracle_response.status == 200
                    else None
                )
                reset_ok = (
                    reset_response.status == 200
                    and reset_oracle_response.status == 200
                    and reset_state == initial_state
                )
                if not _check(
                    checks,
                    "reset_round_trip",
                    reset_ok,
                    "reset restored the exact initial oracle state",
                ):
                    errors.append("fixture reset did not restore the initial state")

                trace_response = _request(
                    f"{session_url}/trace",
                    oracle_token=oracle_token,
                    timeout=timeout,
                )
                trace = trace_response.json() if trace_response.status == 200 else {}
                surface = trace.get("execution_surface", {})
                trace_ok = (
                    trace_response.status == 200
                    and trace.get("task_id") == task_id
                    and trace.get("mode") == mode
                    and surface.get("type") == "hosted_https"
                    and surface.get("public_url") == base_url
                    and surface.get("fixture_version") == health.get("fixture_version")
                    and surface.get("deployment_id") == health.get("deployment_id")
                )
                if not _check(
                    checks,
                    "authenticated_trace",
                    trace_ok,
                    "authenticated trace includes matching execution-surface metadata",
                ):
                    errors.append(
                        "authenticated trace failed or execution-surface metadata mismatched"
                    )

                delete_response = _request(
                    session_url,
                    method="DELETE",
                    oracle_token=oracle_token,
                    timeout=timeout,
                )
                deleted_view = _request(f"{session_url}/view", timeout=timeout)
                cleanup_verified = (
                    delete_response.status == 204 and deleted_view.status == 404
                )
                session_id = None if cleanup_verified else session_id
                if not _check(
                    checks,
                    "session_cleanup",
                    cleanup_verified,
                    "evaluator-authorized deletion removed the temporary session",
                ):
                    errors.append("temporary session cleanup failed")
        else:
            errors.append("session checks skipped because a prerequisite failed")
    except (RuntimeError, ValueError, json.JSONDecodeError) as error:
        errors.append(str(error))
        _check(checks, "request_sequence", False, str(error))
    finally:
        if session_id is not None and oracle_token:
            try:
                cleanup = _request(
                    f"{base_url}/api/sessions/{session_id}",
                    method="DELETE",
                    oracle_token=oracle_token,
                    timeout=timeout,
                )
                cleanup_verified = cleanup.status in {204, 404}
            except RuntimeError:
                cleanup_verified = False
            if not cleanup_verified:
                errors.append("best-effort temporary session cleanup failed")

    passed = bool(checks) and all(check["passed"] for check in checks) and not errors
    report["status"] = "passed" if passed else "failed"
    try:
        _write_report(output_dir, report)
    except OSError as error:
        errors.append(f"could not write {REPORT_FILENAME}: {error}")
        report["status"] = "failed"
        passed = False
    return report, passed
