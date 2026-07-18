from __future__ import annotations

import unittest
from pathlib import Path

from scripts.materialize_project_type_refs import expected_files, synchronize

ROOT = Path(__file__).resolve().parents[1]


class MaterializeProjectTypeReferencesTests(unittest.TestCase):
    def test_materialized_references_match_registry(self) -> None:
        self.assertEqual(synchronize(ROOT, write=False), [])
        self.assertEqual(len(expected_files(ROOT)), 39)

    def test_each_reference_exposes_domain_specific_contract(self) -> None:
        for relative, expected in expected_files(ROOT).items():
            with self.subTest(path=relative.as_posix()):
                actual = (ROOT / relative).read_text(encoding="utf-8")
                self.assertEqual(actual, expected)
                self.assertNotIn("What is the intended output?", actual)


if __name__ == "__main__":
    unittest.main()
