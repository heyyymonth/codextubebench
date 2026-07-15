from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .executable import (
    evaluate_executable_trace,
    load_executable_catalog,
    validate_executable_trace,
)
from .io import write_json
from .preflight import normalize_fixture_url


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _request_json(
    url: str,
    *,
    oracle_token: str,
    method: str = "GET",
    timeout: float = 10.0,
) -> tuple[int, Any]:
    request = Request(
        url,
        method=method,
        headers={
            "Accept": "application/json",
            "X-Oracle-Token": oracle_token,
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except HTTPError as error:
        body = error.read()
        detail = body.decode("utf-8", errors="replace") or str(error.reason)
        raise RuntimeError(f"fixture export request failed with HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"fixture export request failed: {error.reason}") from error


def export_fixture_session(
    *,
    url: str,
    session_id: str,
    trace_output: Path,
    result_output: Path,
    oracle_token_env: str = "CODEXTUBEBENCH_ORACLE_TOKEN",
    expected_revision: str | None = None,
    allow_http_loopback_test: bool = False,
    timeout: float = 10.0,
    delete_after_export: bool = True,
) -> dict[str, Any]:
    base_url = normalize_fixture_url(
        url,
        allow_http_loopback_test=allow_http_loopback_test,
    )
    token = os.environ.get(oracle_token_env, "")
    if not token:
        raise ValueError(
            f"evaluator token environment variable {oracle_token_env} is missing"
        )
    if not session_id.strip():
        raise ValueError("session_id must be non-empty")
    existing_outputs = [path for path in (trace_output, result_output) if path.exists()]
    if existing_outputs:
        raise FileExistsError(
            "refusing to overwrite existing fixture export: "
            + ", ".join(str(path) for path in existing_outputs)
        )

    _, trace = _request_json(
        f"{base_url}/api/sessions/{session_id}/trace",
        oracle_token=token,
        timeout=timeout,
    )
    if not isinstance(trace, dict):
        raise ValueError("fixture trace response must be a JSON object")
    errors = validate_executable_trace(trace)
    if errors:
        raise ValueError("\n".join(errors))
    if expected_revision and trace.get("benchmark_git_revision") != expected_revision:
        raise ValueError("fixture trace benchmark revision does not match expected revision")

    tasks = load_executable_catalog()
    task = next((row for row in tasks if row["id"] == trace.get("task_id")), None)
    if task is None:
        raise ValueError(f"unknown task id in fixture trace: {trace.get('task_id')}")
    evaluated, result = evaluate_executable_trace(task, trace)
    trace_output.parent.mkdir(parents=True, exist_ok=True)
    result_output.parent.mkdir(parents=True, exist_ok=True)
    write_json(trace_output, evaluated)
    write_json(result_output, result)

    deleted = False
    if delete_after_export:
        status, _ = _request_json(
            f"{base_url}/api/sessions/{session_id}",
            oracle_token=token,
            method="DELETE",
            timeout=timeout,
        )
        deleted = status == 204
        if not deleted:
            raise RuntimeError("fixture session deletion did not return HTTP 204")

    return {
        "schema_version": "codextubebench.fixture-session-export.v0.1",
        "task_id": evaluated["task_id"],
        "trace_schema_version": evaluated["schema_version"],
        "result_schema_version": result["schema_version"],
        "benchmark_git_revision": evaluated["benchmark_git_revision"],
        "trace_sha256": _sha256(trace_output),
        "result_sha256": _sha256(result_output),
        "session_deleted": deleted,
    }
