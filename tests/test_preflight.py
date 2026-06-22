import json
import os
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tubebench.executable import validate_executable_trace
from tubebench.fixture_server import (
    FixtureApplication,
    SessionCapacityError,
    ThreadingHTTPServer,
    fixture_startup_metadata,
    hosted_settings_from_environment,
    make_handler,
)
from tubebench.preflight import REPORT_FILENAME, preflight_fixture


@contextmanager
def hosted_test_server(*, dirty: bool = False):
    application = FixtureApplication(
        oracle_token="test-oracle-token",
        benchmark_revision="test-revision",
        benchmark_dirty=dirty,
        deployment_id="test-deployment",
        surface_type="hosted_https",
        session_ttl_seconds=60,
        max_sessions=8,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(application))
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    application.public_base_url = base_url
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield application, base_url
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class HostedSettingsTests(unittest.TestCase):
    def test_hosted_settings_require_https_and_all_runtime_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires environment values"):
            hosted_settings_from_environment({})

        environment = {
            "CODEXTUBEBENCH_ORACLE_TOKEN": "secret-value",
            "CODEXTUBEBENCH_PUBLIC_BASE_URL": "https://fixture.example",
            "CODEXTUBEBENCH_GIT_REVISION": "abc123",
            "CODEXTUBEBENCH_DEPLOYMENT_ID": "deployment-1",
            "PORT": "9000",
        }
        settings = hosted_settings_from_environment(environment)
        self.assertEqual(9000, settings.port)
        self.assertEqual(128, settings.max_sessions)
        self.assertNotIn("secret-value", repr(settings))

        environment["CODEXTUBEBENCH_PUBLIC_BASE_URL"] = "http://fixture.example"
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            hosted_settings_from_environment(environment)

    def test_hosted_startup_metadata_never_contains_oracle_material(self) -> None:
        application = FixtureApplication(
            oracle_token="secret-value",
            benchmark_revision="revision",
            benchmark_dirty=False,
            public_base_url="https://fixture.example",
            deployment_id="deployment-1",
            surface_type="hosted_https",
        )
        metadata = fixture_startup_metadata(
            application,
            hosted=True,
            host="0.0.0.0",
            port=8080,
        )
        self.assertNotIn("oracle_token", metadata)
        self.assertNotIn("secret-value", json.dumps(metadata))

    def test_session_cap_and_ttl_are_enforced(self) -> None:
        now = [100.0]
        application = FixtureApplication(
            oracle_token="token",
            benchmark_revision="revision",
            benchmark_dirty=False,
            max_sessions=1,
            session_ttl_seconds=10,
            clock=lambda: now[0],
        )
        payload = {"task_id": "TCE-002", "mode": "instrumented_browser"}
        application.create_session(payload)
        with self.assertRaises(SessionCapacityError):
            application.create_session(payload)
        now[0] = 111.0
        application.create_session(payload)
        self.assertEqual(1, len(application.sessions))


class HostedFixtureEndpointTests(unittest.TestCase):
    def test_metadata_security_auth_and_cleanup(self) -> None:
        with hosted_test_server() as (application, base_url):
            urlopen(
                f"{base_url}/?preflight=1&task=TCE-002&mode=instrumented_browser"
            ).read()
            self.assertEqual({}, application.sessions)

            health_response = urlopen(f"{base_url}/health")
            health = json.loads(health_response.read())
            self.assertEqual("test-revision", health["benchmark_git_revision"])
            self.assertFalse(health["benchmark_git_dirty"])
            self.assertEqual(12, health["task_count"])
            self.assertIn("Content-Security-Policy", health_response.headers)
            self.assertEqual("DENY", health_response.headers["X-Frame-Options"])
            self.assertIsNone(health_response.headers["Access-Control-Allow-Origin"])
            self.assertNotIn("oracle", json.dumps(health).lower())
            self.assertNotIn(application.oracle_token, json.dumps(health))

            catalog = json.loads(urlopen(f"{base_url}/api/catalog").read())
            self.assertEqual(12, len(catalog["tasks"]))
            for row in catalog["tasks"]:
                self.assertEqual(
                    {"id", "revision", "supported_modes"},
                    set(row),
                )

            create = Request(
                f"{base_url}/api/sessions",
                data=json.dumps(
                    {
                        "task_id": "TCE-002",
                        "mode": "instrumented_browser",
                        "agent": "test-agent",
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            session_id = json.loads(urlopen(create).read())["session_id"]
            trace_url = f"{base_url}/api/sessions/{session_id}/trace"
            with self.assertRaises(HTTPError) as trace_error:
                urlopen(trace_url)
            self.assertEqual(403, trace_error.exception.code)

            authorized_trace = Request(
                trace_url,
                headers={"X-Oracle-Token": "test-oracle-token"},
            )
            trace = json.loads(urlopen(authorized_trace).read())
            self.assertEqual([], validate_executable_trace(trace))
            self.assertEqual(
                {
                    "type": "hosted_https",
                    "public_url": base_url,
                    "fixture_version": "codextubebench-fixture.v0.1",
                    "deployment_id": "test-deployment",
                },
                trace["execution_surface"],
            )

            delete_url = f"{base_url}/api/sessions/{session_id}"
            with self.assertRaises(HTTPError) as delete_error:
                urlopen(Request(delete_url, method="DELETE"))
            self.assertEqual(403, delete_error.exception.code)
            deleted = urlopen(
                Request(
                    delete_url,
                    headers={"X-Oracle-Token": "test-oracle-token"},
                    method="DELETE",
                )
            )
            self.assertEqual(204, deleted.status)
            with self.assertRaises(HTTPError) as missing:
                urlopen(f"{delete_url}/view")
            self.assertEqual(404, missing.exception.code)


class FixturePreflightTests(unittest.TestCase):
    def test_positive_loopback_preflight_is_secret_free_and_cleans_up(self) -> None:
        with hosted_test_server() as (application, base_url):
            with tempfile.TemporaryDirectory() as directory:
                with patch.dict(
                    os.environ,
                    {"CODEXTUBEBENCH_ORACLE_TOKEN": "test-oracle-token"},
                ):
                    report, passed = preflight_fixture(
                        url=base_url,
                        mode="instrumented_browser",
                        task_id="TCE-002",
                        output_dir=Path(directory),
                        expected_revision="test-revision",
                        allow_http_loopback_test=True,
                    )
                self.assertTrue(passed, report)
                self.assertEqual("passed", report["status"])
                self.assertEqual({}, application.sessions)
                report_text = (Path(directory) / REPORT_FILENAME).read_text()
                self.assertNotIn("test-oracle-token", report_text)
                self.assertTrue(
                    all(check["passed"] for check in report["checks"]),
                    report,
                )

    def test_http_requires_explicit_loopback_test_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report, passed = preflight_fixture(
                url="http://127.0.0.1:8765",
                mode="instrumented_browser",
                task_id="TCE-002",
                output_dir=Path(directory),
            )
        self.assertFalse(passed)
        self.assertIn("requires --allow-http-loopback-test", report["errors"][0])

    def test_revision_mismatch_and_missing_token_fail_before_session_creation(self) -> None:
        with hosted_test_server() as (application, base_url):
            with tempfile.TemporaryDirectory() as directory:
                with patch.dict(os.environ, {}, clear=True):
                    report, passed = preflight_fixture(
                        url=base_url,
                        mode="instrumented_browser",
                        task_id="TCE-002",
                        output_dir=Path(directory),
                        expected_revision="wrong-revision",
                        allow_http_loopback_test=True,
                    )
            self.assertFalse(passed)
            self.assertEqual({}, application.sessions)
            failed = {
                check["name"]
                for check in report["checks"]
                if not check["passed"]
            }
            self.assertIn("oracle_token", failed)
            self.assertIn("deployment_metadata", failed)


if __name__ == "__main__":
    unittest.main()
