import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tubebench.fixture_export import export_fixture_session
from tubebench.fixture_server import FixtureApplication, ThreadingHTTPServer, make_handler


class FixtureSessionExportTests(unittest.TestCase):
    def test_export_scores_hashes_and_deletes_without_exposing_token(self) -> None:
        application = FixtureApplication(
            oracle_token="private-evaluator-token",
            benchmark_revision="b" * 40,
            benchmark_dirty=False,
            deployment_id="test-export",
            surface_type="hosted_https",
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(application))
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        application.public_base_url = base_url
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
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
            created = json.loads(urlopen(create).read())
            session_id = created["session_id"]
            urlopen(created["view_url"] if created["view_url"].startswith("http") else base_url + created["view_url"]).read()
            action = Request(
                f"{base_url}/api/sessions/{session_id}/actions",
                data=json.dumps({"type": "pause", "player_id": "player-b"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urlopen(action).read()
            submit = Request(
                f"{base_url}/api/sessions/{session_id}/submit",
                data=json.dumps(
                    {"answer": None, "verifications": ["final_playback_state"]}
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urlopen(submit).read()
            with tempfile.TemporaryDirectory() as directory, patch.dict(
                os.environ,
                {"CODEXTUBEBENCH_ORACLE_TOKEN": "private-evaluator-token"},
            ):
                trace_path = Path(directory) / "trace.json"
                result_path = Path(directory) / "result.json"
                report = export_fixture_session(
                    url=base_url,
                    session_id=session_id,
                    trace_output=trace_path,
                    result_output=result_path,
                    expected_revision="b" * 40,
                    allow_http_loopback_test=True,
                )
                self.assertTrue(report["session_deleted"])
                self.assertEqual(
                    "tubecontrol-executable-trace.v0.2",
                    report["trace_schema_version"],
                )
                self.assertEqual("completed", json.loads(result_path.read_text())["outcome"]["status"])
                self.assertNotIn("private-evaluator-token", json.dumps(report))
                with self.assertRaises(FileExistsError):
                    export_fixture_session(
                        url=base_url,
                        session_id=session_id,
                        trace_output=trace_path,
                        result_output=result_path,
                        expected_revision="b" * 40,
                        allow_http_loopback_test=True,
                    )
                with self.assertRaises(HTTPError) as missing:
                    urlopen(f"{base_url}/api/sessions/{session_id}/view")
                self.assertEqual(404, missing.exception.code)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
