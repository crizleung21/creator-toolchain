from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas/workspace"
TEMPLATE_ROOT = ROOT / "templates/workspace"
EXPECTED = {"workspace","projects","entities","state","session-insights","operator","backlog","surfaces","decisions","rules"}


class WorkspaceSchemaAssetTests(unittest.TestCase):
    def test_all_schema_and_template_assets_exist(self) -> None:
        self.assertEqual({path.stem.removesuffix(".schema") for path in SCHEMA_ROOT.glob("*.schema.json")}, EXPECTED)
        self.assertEqual({path.stem for path in TEMPLATE_ROOT.glob("*.json")}, EXPECTED)

    def test_schemas_target_040(self) -> None:
        for path in SCHEMA_ROOT.glob("*.schema.json"):
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(value["properties"]["schema_version"]["const"], "0.4.0")
                self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_templates_target_040(self) -> None:
        for path in TEMPLATE_ROOT.glob("*.json"):
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(value["schema_version"], "0.4.0")
                self.assertIn("created_at", value)
                self.assertIn("updated_at", value)


if __name__ == "__main__":
    unittest.main()
