import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from release_check import findings


class ReleaseCheckTests(unittest.TestCase):
    def test_detects_secret_and_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bad.md").write_text(
                "Author" + "ization: Bearer top-secret\n"
                + "/Us" + "ers/example/private\n",
                encoding="utf-8",
            )
            problems = findings(root)
            self.assertEqual(2, len(problems))

    def test_clean_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("safe public content\n", encoding="utf-8")
            self.assertEqual([], findings(root))


if __name__ == "__main__":
    unittest.main()
