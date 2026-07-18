from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas/workspace"
TEMPLATE_ROOT = ROOT / "templates/workspace"
STATE_SCHEMAS = {"workspace", "projects", "entities", "state", "session-insights", "operator", "backlog", "surfaces", "decisions", "rules"}
DERIVED_SCHEMAS = {"health-report", "reconciliation-receipt"}


class WorkspaceSchemaAssetTests(unittest.TestCase):
    def test_all_schema_and_template_assets_exist(self) -> None:
        found = {path.stem.removesuffix(".schema") for path in SCHEMA_ROOT.glob("*.schema.json")}
        self.assertEqual(found, STATE_SCHEMAS | DERIVED_SCHEMAS)
        self.assertEqual({path.stem for path in TEMPLATE_ROOT.glob("*.json")}, STATE_SCHEMAS)

    def test_state_surface_schemas_target_040(self) -> None:
        for name in STATE_SCHEMAS:
            path = SCHEMA_ROOT / f"{name}.schema.json"
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(value["properties"]["schema_version"]["const"], "0.4.0")
                self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_derived_schemas_target_100(self) -> None:
        for name in DERIVED_SCHEMAS:
            path = SCHEMA_ROOT / f"{name}.schema.json"
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(value["properties"]["schema_version"]["const"], "1.0.0")
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
