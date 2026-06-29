from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import validate_creator_toolchain as validator


STATE_FILES = (
    "workspace.json",
    "projects.json",
    "entities.json",
    "state.json",
    "session-insights.json",
    "operator.json",
    "backlog.json",
    "surfaces.json",
    "decisions.json",
    "rules.json",
)


class StateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        (self.root / ".creator").mkdir()
        architecture = self.root / "docs/architecture/creator-toolchain.md"
        architecture.parent.mkdir(parents=True)
        architecture.write_text("# Creator Toolchain\n", encoding="utf-8")
        self._write_state()

    def _write_json(self, name: str, value: dict[str, object]) -> None:
        (self.root / ".creator" / name).write_text(
            json.dumps(value, indent=2) + "\n",
            encoding="utf-8",
        )

    def _read_json(self, name: str) -> dict[str, object]:
        return json.loads((self.root / ".creator" / name).read_text(encoding="utf-8"))

    def _write_state(self) -> None:
        common = {
            "schema_version": "0.3.0",
            "owner_skill": "creator-workspace-manager",
            "privacy_class": "repository_workflow_state",
        }
        self._write_json(
            "workspace.json",
            {
                "schema_version": "0.3.0",
                "workspace_id": "creator-toolchain",
                "display_name": "Creator Toolchain",
                "owner_skill": "creator-workspace-manager",
                "privacy_class": "publishable_template",
                "state_contract": ".creator/*.json",
                "architecture_map": "docs/architecture/creator-toolchain.md",
                "active_plan": None,
            },
        )
        self._write_json("projects.json", {**common, "projects": []})
        self._write_json(
            "entities.json",
            {**common, "privacy_class": "private", "entities": []},
        )
        self._write_json(
            "state.json",
            {
                **common,
                "active_projects": [],
                "blocked_projects": [],
                "last_health_check": "2026-06-28",
                "state_divergence": {
                    "score": 0,
                    "level": "green",
                    "notes": "Repository contracts are consistent.",
                },
            },
        )
        self._write_json(
            "session-insights.json",
            {
                **common,
                "privacy_class": "private",
                "entries": [],
                "promotion_policy": "Staged proposals require approval.",
            },
        )
        self._write_json(
            "operator.json",
            {
                **common,
                "privacy_class": "private",
                "owner": "workspace-user",
                "preferences": {"require_evidence_refs": True},
            },
        )
        self._write_json("backlog.json", {**common, "items": []})
        self._write_json(
            "surfaces.json",
            {
                **common,
                "privacy_class": "publishable_template",
                "surfaces": [
                    {"surface_id": name.removesuffix(".json"), "path": f".creator/{name}", "required": True}
                    for name in STATE_FILES
                ],
            },
        )
        self._write_json(
            "decisions.json",
            {
                **common,
                "decisions": [
                    {
                        "decision_id": "DEC-001",
                        "date": "2026-06-28",
                        "title": "Authoritative skill source",
                        "status": "accepted",
                        "rationale": "Keep one source for generated skills.",
                    }
                ],
            },
        )
        self._write_json(
            "rules.json",
            {
                "schema_version": "0.3.0",
                "owner_skill": "creator-rule-router",
                "privacy_class": "repository_contract",
                "domains": [
                    {
                        "domain_id": "GLOBAL",
                        "enabled": True,
                        "priority": 100,
                        "trigger_keywords": [],
                        "rules": [],
                        "commands": [],
                        "exclude_patterns": [],
                        "decision_refs": ["DEC-001"],
                    }
                ],
                "staged_proposals": [],
                "decision_log": [],
            },
        )

    @staticmethod
    def _ids(findings: list[validator.Finding]) -> set[str]:
        return {finding.check_id for finding in findings}

    def test_all_state_files_use_schema_030(self) -> None:
        self.assertEqual(validator.CURRENT_STATE_SCHEMA, "0.3.0")
        self.assertEqual(validator.validate_state_contract(self.root), [])

    def test_workspace_requires_architecture_map(self) -> None:
        workspace = self._read_json("workspace.json")
        workspace.pop("architecture_map")
        self._write_json("workspace.json", workspace)

        findings = validator.validate_state_contract(self.root)

        self.assertIn("STATE_POINTER", self._ids(findings))

    def test_workspace_accepts_null_active_plan(self) -> None:
        findings = validator.validate_state_contract(self.root)

        self.assertNotIn("STATE_POINTER", self._ids(findings))

    def test_empty_projects_are_valid(self) -> None:
        findings = validator.validate_state_contract(self.root)

        self.assertNotIn("STATE_PROJECT", self._ids(findings))

    def test_unknown_active_project_is_rejected(self) -> None:
        state = self._read_json("state.json")
        state["active_projects"] = ["missing"]
        self._write_json("state.json", state)

        findings = validator.validate_state_contract(self.root)

        self.assertIn("STATE_PROJECT", self._ids(findings))

    def test_required_surface_target_must_exist(self) -> None:
        (self.root / ".creator/entities.json").unlink()

        findings = validator.validate_state_contract(self.root)

        self.assertIn("STATE_REQUIRED", self._ids(findings))
        self.assertIn("STATE_POINTER", self._ids(findings))

    def test_rule_decision_reference_must_exist(self) -> None:
        rules = self._read_json("rules.json")
        rules["domains"][0]["decision_refs"] = ["DEC-999"]
        self._write_json("rules.json", rules)

        findings = validator.validate_state_contract(self.root)

        self.assertIn("RULE_DECISION_REF", self._ids(findings))

    def test_private_surface_rejects_publishable_privacy_class(self) -> None:
        entities = self._read_json("entities.json")
        entities["privacy_class"] = "publishable_template"
        self._write_json("entities.json", entities)

        findings = validator.validate_state_contract(self.root)

        self.assertIn("STATE_PRIVACY", self._ids(findings))


if __name__ == "__main__":
    unittest.main()
