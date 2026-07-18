from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas/project"
TEMPLATE_ROOT = ROOT / "templates/project"


class ProjectSchemaAssetTests(unittest.TestCase):
    def test_required_schemas_exist(self) -> None:
        self.assertEqual(
            {path.name for path in SCHEMA_ROOT.glob("*.schema.json")},
            {"project.schema.json", "intake-state.schema.json", "handoff.schema.json", "ledger-event.schema.json"},
        )

    def test_schemas_use_draft_2020_12(self) -> None:
        for path in SCHEMA_ROOT.glob("*.schema.json"):
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertFalse(value["additionalProperties"])

    def test_canonical_templates_exist(self) -> None:
        self.assertEqual(
            {path.name for path in TEMPLATE_ROOT.iterdir() if path.is_file()},
            {"project.json", "INTAKE-STATE.md", "PLANNING.md", "DECISIONS.md", "OPEN-QUESTIONS.md", "HANDOFF.md"},
        )


if __name__ == "__main__":
    unittest.main()
