from __future__ import annotations

import argparse
import json
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .executable import FixtureSession, load_executable_catalog


class FixtureApplication:
    def __init__(
        self,
        *,
        catalog_path: Path | None = None,
        static_dir: Path | None = None,
        oracle_token: str | None = None,
    ) -> None:
        tasks = load_executable_catalog(catalog_path)
        self.tasks = {task["id"]: task for task in tasks}
        self.static_dir = static_dir or (
            Path(__file__).resolve().parents[2] / "fixtures" / "longform_player"
        )
        self.oracle_token = oracle_token or secrets.token_urlsafe(24)
        self.sessions: dict[str, FixtureSession] = {}

    def create_session(self, payload: dict[str, Any]) -> FixtureSession:
        task_id = payload.get("task_id")
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"unknown task id: {task_id}")
        mode = payload.get("mode") or task["default_mode"]
        agent = str(payload.get("agent") or "manual-agent")
        session = FixtureSession(task, mode, agent)
        self.sessions[session.run_id] = session
        return session


def make_handler(application: FixtureApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "CodexTubeBenchFixture/0.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

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
            if length > 1_000_000:
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
            return application.sessions.get(parts[2]), parts[3]

        def _authorized_oracle(self) -> bool:
            return secrets.compare_digest(
                self.headers.get("X-Oracle-Token", ""),
                application.oracle_token,
            )

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/health":
                self._json(HTTPStatus.OK, {"status": "ok"})
                return
            session, route = self._session_route()
            if session is not None and route == "view":
                self._json(HTTPStatus.OK, session.view())
                return
            if session is not None and route in {"oracle", "trace"}:
                if not self._authorized_oracle():
                    self._json(HTTPStatus.FORBIDDEN, {"error": "oracle token required"})
                    return
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
                if route == "actions":
                    view = session.apply(self._body())
                    self._json(HTTPStatus.OK, view)
                    return
                if route == "submit":
                    body = self._body()
                    session.submit(body.get("answer"), body.get("verifications", []))
                    self._json(HTTPStatus.OK, {"accepted": True})
                    return
                if route == "reset":
                    session.reset()
                    self._json(HTTPStatus.OK, session.view())
                    return
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

    return Handler


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    catalog_path: Path | None = None,
    oracle_token: str | None = None,
) -> None:
    application = FixtureApplication(
        catalog_path=catalog_path,
        oracle_token=oracle_token,
    )
    server = ThreadingHTTPServer((host, port), make_handler(application))
    actual_port = server.server_address[1]
    print(
        json.dumps(
            {
                "base_url": f"http://{host}:{actual_port}",
                "oracle_token": application.oracle_token,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic CodexTubeBench player fixture"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--oracle-token")
    args = parser.parse_args()
    serve(
        host=args.host,
        port=args.port,
        catalog_path=args.catalog,
        oracle_token=args.oracle_token,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
