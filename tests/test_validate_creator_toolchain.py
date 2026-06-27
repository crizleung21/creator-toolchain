from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import validate_creator_toolchain as validator


ROOT = Path(__file__).resolve().parents[1]


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.temp_root = Path(self.tempdir.name)

    def _copy(self, relative: str) -> None:
        source = ROOT / relative
        destination = self.temp_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)

    def _state_root(self) -> Path:
        self._copy(".creator")
        self._copy("docs/source-analysis")
        return self.temp_root

    def _plugin_root(self) -> Path:
        self._copy(".agents/skills")
        self._copy(".agents/plugins/marketplace.json")
        self._copy("plugin/creator-toolchain")
        return self.temp_root

    @staticmethod
    def _ids(findings: list[validator.Finding]) -> set[str]:
        return {finding.check_id for finding in findings}

    def test_scope_repo_passes_current_repository(self) -> None:
        self.assertEqual(validator.validate_repo_contract(ROOT), [])

    def test_scope_state_rejects_broken_pointer(self) -> None:
        root = self._state_root()
        workspace_path = root / ".creator/workspace.json"
        workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
        workspace["active_plan"] = "missing-plan.md"
        workspace_path.write_text(json.dumps(workspace), encoding="utf-8")

        findings = validator.validate_state_contract(root)

        self.assertIn("STATE_POINTER", self._ids(findings))

    def test_scope_state_rejects_invalid_jsonl_line(self) -> None:
        root = self._state_root()
        ledger = root / ".creator/plans/creator-toolchain-implementation/activity_ledger.jsonl"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write("{invalid}\n")

        findings = validator.validate_state_contract(root)

        self.assertIn("STATE_JSONL", self._ids(findings))

    def test_scope_state_requires_global_rule_domain(self) -> None:
        root = self._state_root()
        rules_path = root / ".creator/rules.json"
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        rules["domains"] = [domain for domain in rules["domains"] if domain["domain_id"] != "GLOBAL"]
        rules_path.write_text(json.dumps(rules), encoding="utf-8")

        findings = validator.validate_state_contract(root)

        self.assertIn("RULE_GLOBAL", self._ids(findings))

    def test_scope_state_rejects_legacy_schema_version(self) -> None:
        root = self._state_root()
        workspace_path = root / ".creator/workspace.json"
        workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
        workspace["schema_version"] = "0.1.0"
        workspace_path.write_text(json.dumps(workspace), encoding="utf-8")

        findings = validator.validate_state_contract(root)

        self.assertIn("STATE_SCHEMA_VERSION", self._ids(findings))

    def test_scope_state_requires_creator_native_health_fields(self) -> None:
        root = self._state_root()
        state_path = root / ".creator/state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.pop("last_health_check", None)
        state.pop("state_divergence", None)
        state_path.write_text(json.dumps(state), encoding="utf-8")

        findings = validator.validate_state_contract(root)

        self.assertIn("STATE_FIELD", self._ids(findings))

    def test_scope_state_allows_active_project_without_summary(self) -> None:
        root = self._state_root()
        projects_path = root / ".creator/projects.json"
        projects = json.loads(projects_path.read_text(encoding="utf-8"))
        active_project = next(
            project
            for project in projects["projects"]
            if project["project_id"] == "creator-toolchain-naming-migration"
        )
        active_project.pop("last_summary", None)
        projects_path.write_text(json.dumps(projects), encoding="utf-8")

        findings = validator.validate_state_contract(root)

        self.assertNotIn("STATE_POINTER", self._ids(findings))

    def test_scope_plugin_rejects_private_state(self) -> None:
        root = self._plugin_root()
        private = root / "plugin/creator-toolchain/.creator/private.json"
        private.parent.mkdir(parents=True)
        private.write_text("{}\n", encoding="utf-8")

        findings = validator.validate_plugin_package(root)

        self.assertIn("PACKAGE_PRIVATE", self._ids(findings))

    def test_scope_plugin_rejects_ds_store(self) -> None:
        root = self._plugin_root()
        (root / "plugin/creator-toolchain/.DS_Store").write_text("junk", encoding="utf-8")

        findings = validator.validate_plugin_package(root)

        self.assertIn("PACKAGE_ARTIFACT", self._ids(findings))

    def test_scope_plugin_rejects_local_override(self) -> None:
        root = self._plugin_root()
        override = root / "plugin/creator-toolchain/settings.local.json"
        override.write_text("{}\n", encoding="utf-8")

        findings = validator.validate_plugin_package(root)

        self.assertIn("PACKAGE_PRIVATE", self._ids(findings))

    def test_scope_plugin_rejects_package_directory_and_zip(self) -> None:
        root = self._plugin_root()
        package_dir = root / "plugin/creator-toolchain/package"
        package_dir.mkdir()
        (package_dir / "creator-toolchain.zip").write_bytes(b"archive")

        findings = validator.validate_plugin_package(root)

        self.assertIn("PACKAGE_ARTIFACT", self._ids(findings))

    def test_scope_plugin_rejects_extra_mirror_file(self) -> None:
        root = self._plugin_root()
        extra = root / "plugin/creator-toolchain/skills/creator-execution-cycle/extra.md"
        self.assertTrue(extra.parent.is_dir())
        extra.write_text("extra\n", encoding="utf-8")

        findings = validator.validate_plugin_package(root)

        self.assertIn("MIRROR_PARITY", self._ids(findings))

    def test_scope_repo_rejects_invalid_skill_frontmatter(self) -> None:
        for relative in [
            ".agents/skills",
            "AGENTS.md",
            "README.md",
            "docs/source-analysis",
            "docs/qa",
            "scripts/materialize_project_type_refs.py",
            "scripts/sync_plugin_skills.py",
            "scripts/validate_creator_toolchain.py",
        ]:
            self._copy(relative)
        skill = self.temp_root / ".agents/skills/creator-execution-cycle/SKILL.md"
        self.assertTrue(skill.is_file())
        skill.write_text("# Missing frontmatter\n", encoding="utf-8")

        findings = validator.validate_repo_contract(self.temp_root)

        self.assertIn("SKILL_FRONTMATTER", self._ids(findings))

    def test_scope_repo_requires_all_seven_skills(self) -> None:
        for relative in [
            ".agents/skills",
            "AGENTS.md",
            "README.md",
            "docs/source-analysis",
            "docs/qa",
            "scripts/materialize_project_type_refs.py",
            "scripts/sync_plugin_skills.py",
            "scripts/validate_creator_toolchain.py",
        ]:
            self._copy(relative)
        skill_root = self.temp_root / ".agents/skills/creator-evidence-audit"
        self.assertTrue(skill_root.is_dir())
        shutil.rmtree(skill_root)

        findings = validator.validate_repo_contract(self.temp_root)

        self.assertIn("REPO_SKILL_COUNT", self._ids(findings))

    def test_scope_repo_requires_all_thirteen_project_types(self) -> None:
        for relative in [
            ".agents/skills",
            "AGENTS.md",
            "README.md",
            "docs/source-analysis",
            "docs/qa",
            "scripts/materialize_project_type_refs.py",
            "scripts/sync_plugin_skills.py",
            "scripts/validate_creator_toolchain.py",
        ]:
            self._copy(relative)
        missing_type = self.temp_root / ".agents/skills/creator-intake-planner/references/types/utility"
        self.assertTrue(missing_type.is_dir())
        shutil.rmtree(missing_type)

        findings = validator.validate_repo_contract(self.temp_root)

        self.assertIn("PROJECT_TYPE_COUNT", self._ids(findings))

    def test_scope_repo_rejects_legacy_product_marker(self) -> None:
        for relative in [
            ".agents/skills",
            "AGENTS.md",
            "README.md",
            "docs/source-analysis",
            "docs/qa",
            "scripts/materialize_project_type_refs.py",
            "scripts/sync_plugin_skills.py",
            "scripts/validate_creator_toolchain.py",
        ]:
            self._copy(relative)
        marker = "creator-" + "paul-loop"
        (self.temp_root / "README.md").write_text(f"Legacy marker: {marker}\n", encoding="utf-8")

        findings = validator.validate_repo_contract(self.temp_root)

        self.assertIn("LEGACY_NAME", self._ids(findings))

    def test_scope_all_aggregates_failures(self) -> None:
        findings = validator.validate_all(self.temp_root)

        self.assertEqual({finding.scope for finding in findings}, {"repo", "state", "plugin"})

    def test_invalid_scope_exits_two(self) -> None:
        self.assertEqual(validator.main(["--scope", "invalid"]), 2)


if __name__ == "__main__":
    unittest.main()
