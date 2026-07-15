from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

from .executable import (
    SUITE_ID,
    TRACE_SCHEMA_VERSION,
    TRACE_SCHEMA_VERSION_V2,
    FixtureSession,
    benchmark_provenance,
    catalog_digest,
    load_executable_catalog,
)

FIXTURE_VERSION = "codextubebench-fixture.v0.2"
DEFAULT_HOSTED_PORT = 8080
DEFAULT_SESSION_TTL_SECONDS = 3600
DEFAULT_MAX_SESSIONS = 128
HOSTED_REQUIRED_ENV = (
    "CODEXTUBEBENCH_ORACLE_TOKEN",
    "CODEXTUBEBENCH_PUBLIC_BASE_URL",
    "CODEXTUBEBENCH_GIT_REVISION",
    "CODEXTUBEBENCH_DEPLOYMENT_ID",
)


class SessionCapacityError(RuntimeError):
    pass


@dataclass(frozen=True)
class HostedSettings:
    oracle_token: str = field(repr=False)
    public_base_url: str
    benchmark_revision: str
    deployment_id: str
    port: int
    session_ttl_seconds: int
    max_sessions: int


@dataclass
class SessionRecord:
    session: FixtureSession
    created_at: float
    last_accessed_at: float


def _positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return parsed


def _is_loopback_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return (
        parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        and not parsed.username
        and not parsed.password
    )


def hosted_settings_from_environment(
    environment: Mapping[str, str] | None = None,
    *,
    allow_http_loopback_test: bool = False,
) -> HostedSettings:
    env = environment or os.environ
    missing = [name for name in HOSTED_REQUIRED_ENV if not env.get(name, "").strip()]
    if missing:
        raise ValueError(
            "hosted mode requires environment values: " + ", ".join(missing)
        )

    public_base_url = env["CODEXTUBEBENCH_PUBLIC_BASE_URL"].strip().rstrip("/")
    parsed = urlparse(public_base_url)
    allowed_test_url = allow_http_loopback_test and _is_loopback_http_url(
        public_base_url
    )
    if parsed.scheme != "https" and not allowed_test_url:
        raise ValueError(
            "CODEXTUBEBENCH_PUBLIC_BASE_URL must use HTTPS; "
            "loopback HTTP is allowed only with --allow-http-loopback-test"
        )
    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError(
            "CODEXTUBEBENCH_PUBLIC_BASE_URL must be a credential-free origin URL"
        )

    return HostedSettings(
        oracle_token=env["CODEXTUBEBENCH_ORACLE_TOKEN"],
        public_base_url=public_base_url,
        benchmark_revision=env["CODEXTUBEBENCH_GIT_REVISION"].strip(),
        deployment_id=env["CODEXTUBEBENCH_DEPLOYMENT_ID"].strip(),
        port=_positive_int(env.get("PORT", str(DEFAULT_HOSTED_PORT)), "PORT"),
        session_ttl_seconds=_positive_int(
            env.get(
                "CODEXTUBEBENCH_SESSION_TTL_SECONDS",
                str(DEFAULT_SESSION_TTL_SECONDS),
            ),
            "CODEXTUBEBENCH_SESSION_TTL_SECONDS",
        ),
        max_sessions=_positive_int(
            env.get("CODEXTUBEBENCH_MAX_SESSIONS", str(DEFAULT_MAX_SESSIONS)),
            "CODEXTUBEBENCH_MAX_SESSIONS",
        ),
    )


class FixtureApplication:
    def __init__(
        self,
        *,
        catalog_path: Path | None = None,
        static_dir: Path | None = None,
        oracle_token: str | None = None,
        benchmark_revision: str | None = None,
        benchmark_dirty: bool | None = None,
        public_base_url: str | None = None,
        deployment_id: str = "local",
        surface_type: str = "local",
        session_ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        tasks = load_executable_catalog(catalog_path)
        self.tasks = {task["id"]: task for task in tasks}
        self.catalog_digest = catalog_digest(tasks)
        self.static_dir = static_dir or (
            Path(__file__).resolve().parents[2] / "fixtures" / "longform_player"
        )
        self.oracle_token = oracle_token or secrets.token_urlsafe(24)
        explicit_benchmark_revision = benchmark_revision is not None
        if benchmark_revision is None:
            benchmark_revision, detected_dirty = benchmark_provenance()
            if benchmark_dirty is None:
                benchmark_dirty = detected_dirty
        self.benchmark_revision = benchmark_revision
        self.benchmark_dirty = benchmark_dirty
        self.session_benchmark_revision = (
            benchmark_revision if explicit_benchmark_revision else None
        )
        self.session_benchmark_dirty = (
            benchmark_dirty if explicit_benchmark_revision else None
        )
        self.public_base_url = public_base_url
        self.deployment_id = deployment_id
        self.surface_type = surface_type
        self.session_ttl_seconds = session_ttl_seconds
        self.max_sessions = max_sessions
        self.clock = clock
        self.sessions: dict[str, SessionRecord] = {}
        self.lock = threading.RLock()

    @property
    def execution_surface(self) -> dict[str, Any] | None:
        if self.surface_type != "hosted_https" or self.public_base_url is None:
            return None
        return {
            "type": "hosted_https",
            "public_url": self.public_base_url,
            "fixture_version": FIXTURE_VERSION,
            "deployment_id": self.deployment_id,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "suite": SUITE_ID,
            "benchmark_git_revision": self.benchmark_revision,
            "benchmark_git_dirty": self.benchmark_dirty,
            "fixture_version": FIXTURE_VERSION,
            "deployment_id": self.deployment_id,
            "catalog_digest": self.catalog_digest,
            "task_count": len(self.tasks),
        }

    def catalog_summary(self) -> dict[str, Any]:
        return {
            "tasks": [
                {
                    "id": task["id"],
                    "revision": task["revision"],
                    "supported_modes": task["supported_modes"],
                }
                for task in self.tasks.values()
            ]
        }

    def _prune_expired_locked(self, now: float) -> None:
        expired = [
            session_id
            for session_id, record in self.sessions.items()
            if now - record.last_accessed_at >= self.session_ttl_seconds
        ]
        for session_id in expired:
            del self.sessions[session_id]

    def create_session(self, payload: dict[str, Any]) -> FixtureSession:
        task_id = payload.get("task_id")
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"unknown task id: {task_id}")
        mode = payload.get("mode") or task["default_mode"]
        agent = str(payload.get("agent") or "manual-agent")
        session = FixtureSession(
            task,
            mode,
            agent,
            benchmark_revision=self.session_benchmark_revision,
            benchmark_dirty=self.session_benchmark_dirty,
            execution_surface=self.execution_surface,
            trace_version=(
                TRACE_SCHEMA_VERSION_V2
                if self.surface_type == "hosted_https"
                else TRACE_SCHEMA_VERSION
            ),
        )
        with self.lock:
            now = self.clock()
            self._prune_expired_locked(now)
            if len(self.sessions) >= self.max_sessions:
                raise SessionCapacityError(
                    "fixture session capacity reached; retry after a session expires"
                )
            self.sessions[session.run_id] = SessionRecord(session, now, now)
        return session

    def get_session(self, session_id: str) -> FixtureSession | None:
        with self.lock:
            now = self.clock()
            self._prune_expired_locked(now)
            record = self.sessions.get(session_id)
            if record is None:
                return None
            record.last_accessed_at = now
            return record.session

    def delete_session(self, session_id: str) -> bool:
        with self.lock:
            self._prune_expired_locked(self.clock())
            return self.sessions.pop(session_id, None) is not None


def make_handler(application: FixtureApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "TubeBenchFixture/0.2"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def end_headers(self) -> None:
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            )
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            if application.surface_type == "hosted_https":
                self.send_header("Strict-Transport-Security", "max-age=31536000")
            super().end_headers()

        def _json(self, status: int, value: Any) -> None:
            payload = json.dumps(value, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def _body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 1_000_000:
                raise ValueError("request body exceeds 1 MB")
            raw = self.rfile.read(length)
            if not raw:
                return {}
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("request body must be a JSON object")
            return value

        def _session_route(self) -> tuple[FixtureSession | None, str | None]:
            parts = [part for part in urlparse(self.path).path.split("/") if part]
            if len(parts) != 4 or parts[:2] != ["api", "sessions"]:
                return None, None
            return application.get_session(parts[2]), parts[3]

        def _session_id(self) -> str | None:
            parts = [part for part in urlparse(self.path).path.split("/") if part]
            if len(parts) != 3 or parts[:2] != ["api", "sessions"]:
                return None
            return parts[2]

        def _authorized_oracle(self) -> bool:
            return secrets.compare_digest(
                self.headers.get("X-Oracle-Token", ""),
                application.oracle_token,
            )

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/health":
                self._json(HTTPStatus.OK, application.health())
                return
            if path == "/api/catalog":
                self._json(HTTPStatus.OK, application.catalog_summary())
                return
            session, route = self._session_route()
            if session is not None and route == "view":
                with application.lock:
                    self._json(HTTPStatus.OK, session.view())
                return
            if session is not None and route in {"oracle", "trace"}:
                if not self._authorized_oracle():
                    self._json(HTTPStatus.FORBIDDEN, {"error": "oracle token required"})
                    return
                with application.lock:
                    value = (
                        session.oracle_state()
                        if route == "oracle"
                        else session.trace()
                    )
                self._json(HTTPStatus.OK, value)
                return
            asset = "index.html" if path == "/" else path.lstrip("/")
            if asset not in {"index.html", "app.js", "styles.css"}:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            file_path = application.static_dir / asset
            if not file_path.is_file():
                self._json(HTTPStatus.NOT_FOUND, {"error": "asset missing"})
                return
            content = file_path.read_bytes()
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
            }[file_path.suffix]
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self) -> None:
            try:
                path = urlparse(self.path).path
                if path == "/api/sessions":
                    session = application.create_session(self._body())
                    self._json(
                        HTTPStatus.CREATED,
                        {
                            "session_id": session.run_id,
                            "view_url": f"/api/sessions/{session.run_id}/view",
                        },
                    )
                    return
                session, route = self._session_route()
                if session is None:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "session not found"})
                    return
                if (
                    route == "reset"
                    and application.surface_type == "hosted_https"
                    and not self._authorized_oracle()
                ):
                    self._json(HTTPStatus.FORBIDDEN, {"error": "oracle token required"})
                    return
                with application.lock:
                    if route == "actions":
                        view = session.apply(self._body())
                        self._json(HTTPStatus.OK, view)
                        return
                    if route == "submit":
                        body = self._body()
                        session.submit(
                            body.get("answer"),
                            body.get("verifications", []),
                            body.get("qualitative_report"),
                        )
                        self._json(HTTPStatus.OK, {"accepted": True})
                        return
                    if route == "reset":
                        session.reset()
                        self._json(HTTPStatus.OK, session.view())
                        return
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            except SessionCapacityError as error:
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(error)})
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

        def do_DELETE(self) -> None:
            session_id = self._session_id()
            if session_id is None:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            if not self._authorized_oracle():
                self._json(HTTPStatus.FORBIDDEN, {"error": "oracle token required"})
                return
            if not application.delete_session(session_id):
                self._json(HTTPStatus.NOT_FOUND, {"error": "session not found"})
                return
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

    return Handler


def fixture_startup_metadata(
    application: FixtureApplication,
    *,
    hosted: bool,
    host: str,
    port: int,
) -> dict[str, Any]:
    metadata = {
        "base_url": (
            application.public_base_url
            if hosted
            else f"http://{host}:{port}"
        ),
        "deployment_id": application.deployment_id,
        "fixture_version": FIXTURE_VERSION,
    }
    if hosted:
        metadata["benchmark_git_revision"] = application.benchmark_revision
        metadata["benchmark_git_dirty"] = application.benchmark_dirty
    else:
        metadata["oracle_token"] = application.oracle_token
    return metadata


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    catalog_path: Path | None = None,
    oracle_token: str | None = None,
    hosted: bool = False,
    allow_http_loopback_test: bool = False,
) -> None:
    if hosted:
        settings = hosted_settings_from_environment(
            allow_http_loopback_test=allow_http_loopback_test
        )
        host = "0.0.0.0"
        port = settings.port
        application = FixtureApplication(
            catalog_path=catalog_path,
            oracle_token=settings.oracle_token,
            benchmark_revision=settings.benchmark_revision,
            benchmark_dirty=False,
            public_base_url=settings.public_base_url,
            deployment_id=settings.deployment_id,
            surface_type="hosted_https",
            session_ttl_seconds=settings.session_ttl_seconds,
            max_sessions=settings.max_sessions,
        )
    else:
        application = FixtureApplication(
            catalog_path=catalog_path,
            oracle_token=oracle_token,
        )

    server = ThreadingHTTPServer((host, port), make_handler(application))
    actual_port = server.server_address[1]
    startup = fixture_startup_metadata(
        application,
        hosted=hosted,
        host=host,
        port=actual_port,
    )
    print(json.dumps(startup, sort_keys=True), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic TubeBench player fixture"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--oracle-token")
    parser.add_argument("--hosted", action="store_true")
    parser.add_argument(
        "--allow-http-loopback-test",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    serve(
        host=args.host,
        port=args.port,
        catalog_path=args.catalog,
        oracle_token=args.oracle_token,
        hosted=args.hosted,
        allow_http_loopback_test=args.allow_http_loopback_test,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
