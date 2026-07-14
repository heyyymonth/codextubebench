import unittest
import json
from pathlib import Path

from scripts.validate_paper_artifact import validate


ROOT = Path(__file__).resolve().parents[1]


class PaperEndpointTests(unittest.TestCase):
    def test_public_paper_endpoint_opens_pdf_artifact(self) -> None:
        pdf = ROOT / "docs" / "paper" / "tubebench.pdf"
        index = (ROOT / "docs" / "paper" / "index.html").read_text(encoding="utf-8")
        fixture = (ROOT / "docs" / "static-fixture" / "index.html").read_text(
            encoding="utf-8"
        )

        self.assertTrue(pdf.is_file())
        self.assertGreater(pdf.stat().st_size, 0)
        self.assertEqual(b"%PDF", pdf.read_bytes()[:4])
        self.assertIn("tubebench.pdf", index)
        self.assertIn('href="./paper/tubebench.pdf"', fixture)
        self.assertIn('data-testid="research-paper-link"', fixture)

    def test_public_paper_provenance_matches_pdf(self) -> None:
        provenance = json.loads(
            (ROOT / "docs/paper/provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], validate())
        self.assertEqual(
            "tubebench.paper-artifact-provenance.v1",
            provenance["schema_version"],
        )
        self.assertFalse(provenance["paper_source_dirty"])


if __name__ == "__main__":
    unittest.main()
