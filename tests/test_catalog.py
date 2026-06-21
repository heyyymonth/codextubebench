import unittest

from tubebench.catalog import load_catalog, validate_catalog


class CatalogTests(unittest.TestCase):
    def test_pilot_catalog_is_valid(self) -> None:
        tasks = load_catalog()
        self.assertEqual(24, len(tasks))
        self.assertEqual([], validate_catalog(tasks))


if __name__ == "__main__":
    unittest.main()
