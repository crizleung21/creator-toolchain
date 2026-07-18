from __future__ import annotations

import unittest
from pathlib import Path

from scripts.creator_project_types import EXPECTED_TYPES, get_project_type, load_project_types

ROOT = Path(__file__).resolve().parents[1]


class CreatorProjectTypeTests(unittest.TestCase):
    def test_registry_contains_exactly_thirteen_types(self) -> None:
        types = load_project_types(ROOT)
        self.assertEqual(set(types), EXPECTED_TYPES)
        self.assertEqual(len(types), 13)

    def test_contracts_are_domain_specific_and_execution_handed_off(self) -> None:
        types = load_project_types(ROOT)
        purposes = {item["purpose"] for item in types.values()}
        self.assertEqual(len(purposes), 13)
        for type_id, item in types.items():
            with self.subTest(type_id=type_id):
                self.assertEqual(item["default_handoff"], "creator-execution-cycle")
                self.assertGreaterEqual(len(item["inputs"]), 3)
                self.assertGreaterEqual(len(item["deliverables"]), 3)
                self.assertGreaterEqual(len(item["acceptance_patterns"]), 3)
                self.assertGreaterEqual(len(item["risk_checklist"]), 3)

    def test_unknown_type_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            get_project_type("unknown", ROOT)


if __name__ == "__main__":
    unittest.main()
