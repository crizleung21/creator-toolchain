from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas/execution"
TEMPLATE_ROOT = ROOT / "templates/execution"


class ExecutionSchemaAssetTests(unittest.TestCase):
    def test_required_execution_schemas_exist(self) -> None:
        self.assertEqual(
            {path.name for path in SCHEMA_ROOT.glob("*.schema.json")},
            {
                "execution-state.schema.json",
                "task.schema.json",
                "reconciliation.schema.json",
                "state-update-proposal.schema.json",
            },
        )

    def test_execution_schemas_use_supported_contract(self) -> None:
        for path in SCHEMA_ROOT.glob("*.schema.json"):
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    value["$schema"],
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertFalse(value["additionalProperties"])
                self.assertEqual(
                    value["properties"]["schema_version"]["const"],
                    "1.0.0",
                )

    def test_execution_templates_exist(self) -> None:
        self.assertEqual(
            {path.name for path in TEMPLATE_ROOT.glob("*.json")},
            {"execution-state.json", "tasks.json"},
        )

    def test_execution_runtime_modules_exist(self) -> None:
        self.assertTrue((ROOT / "scripts/creator_execution_lifecycle.py").is_file())
        self.assertTrue((ROOT / "scripts/creator_execution_closure.py").is_file())


if __name__ == "__main__":
    unittest.main()
