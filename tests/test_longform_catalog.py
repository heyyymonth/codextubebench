import unittest
from copy import deepcopy

from tubebench.longform_catalog import load_longform_catalog, validate_longform_catalog


class LongFormCatalogTests(unittest.TestCase):
    def test_seed_catalog_is_valid(self) -> None:
        tasks = load_longform_catalog()
        self.assertEqual(10, len(tasks))
        self.assertEqual([], validate_longform_catalog(tasks))

    def test_unknown_evidence_media_is_rejected(self) -> None:
        tasks = deepcopy(load_longform_catalog())
        tasks[0]["ground_truth"]["evidence_obligations"][0]["alternatives"][0][0][
            "media_id"
        ] = "missing"
        errors = validate_longform_catalog(tasks)
        self.assertTrue(any("evidence atom references unknown media" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
