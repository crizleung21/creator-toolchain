from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.creator_rule_store import REQUIRED_DOMAINS, validate_rules_document

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas/rules"
EXPECTED = {"domain.schema.json", "rule.schema.json", "command.schema.json", "proposal.schema.json", "decision-entry.schema.json", "conflict-report.schema.json"}


class RuleSchemaAssetTests(unittest.TestCase):
    def test_required_rule_schemas_exist(self) -> None:
        self.assertEqual({path.name for path in SCHEMA_ROOT.glob("*.schema.json")}, EXPECTED)

    def test_rule_schemas_use_supported_contract(self) -> None:
        for path in SCHEMA_ROOT.glob("*.schema.json"):
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8")); self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema"); self.assertFalse(value["additionalProperties"])

    def test_live_rules_document_is_valid_and_domains_are_real(self) -> None:
        document = json.loads((ROOT / ".creator/rules.json").read_text(encoding="utf-8")); self.assertEqual(validate_rules_document(ROOT, document, schema_root=ROOT), []); self.assertEqual(REQUIRED_DOMAINS - {item["domain_id"] for item in document["domains"]}, set())


if __name__ == "__main__": unittest.main()
