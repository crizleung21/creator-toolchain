from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import validate_creator_toolchain as validator
from scripts.package_integrity import build_integrity_report
from scripts.sync_plugin_skills import SKILLS


ROOT = Path(__file__).resolve().parents[1]


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.temp_root = Path(self.tempdir.name)

    @staticmethod
    def _ids(findings: list[validator.Finding]) -> set[str]:
        return {finding.check_id for finding in findings}

    def _plugin_root(self) -> Path:
        root = self.temp_root
        package = root / "plugin/creator-toolchain"
        source_root = root / ".agents/skills"
        (package / ".codex-plugin").mkdir(parents=True)
        (package / "skills").mkdir()
        (root / ".agents/plugins").mkdir(parents=True)
        manifest = {
            "name": "creator-toolchain",
            "version": "1.0.1",
            "description": "Creator Toolchain",
            "author": {"name": "crizleung21"},
            "license": "MIT",
            "skills": "./skills/",
            "interface": {"developerName": "crizleung21"},
        }
        (package / ".codex-plugin/plugin.json").write_text(
            json.dumps(manifest) + "\n",
            encoding="utf-8",
        )
        marketplace = {
            "name": "creator-toolchain",
            "plugins": [
                {
                    "name": "creator-toolchain",
                    "source": {"source": "local", "path": "./plugin/creator-toolchain"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Productivity",
                }
            ],
        }
        (root / ".agents/plugins/marketplace.json").write_text(
            json.dumps(marketplace) + "\n",
            encoding="utf-8",
        )
        for relative in ("README.md", "CHANGELOG.md", "LICENSE"):
            (package / relative).write_text(f"{relative}\n", encoding="utf-8")
        (root / "LICENSE").write_text("LICENSE\n", encoding="utf-8")
        for skill in SKILLS:
            source = source_root / skill
            plugin = package / "skills" / skill
            source.mkdir(parents=True)
            plugin.mkdir(parents=True)
            content = f"---\nname: {skill}\ndescription: test\n---\n"
            (source / "SKILL.md").write_text(content, encoding="utf-8")
            (plugin / "SKILL.md").write_text(content, encoding="utf-8")
        report_path = root / "docs/qa/package-integrity-report.json"
        report_path.parent.mkdir(parents=True)
        report_path.write_text(
            json.dumps(build_integrity_report(root, package), indent=2) + "\n",
            encoding="utf-8",
        )
        return root

    def test_scope_repo_passes_current_repository(self) -> None:
        self.assertEqual(validator.validate_repo_contract(ROOT), [])

    def test_scope_plugin_passes_current_contract(self) -> None:
        root = self._plugin_root()

        self.assertEqual(validator.validate_plugin_package(root), [])

    def test_scope_plugin_rejects_unexpected_package_file(self) -> None:
        root = self._plugin_root()
        (root / "plugin/creator-toolchain/unexpected.md").write_text("bad\n", encoding="utf-8")

        findings = validator.validate_plugin_package(root)

        self.assertIn("PACKAGE_INTEGRITY", self._ids(findings))

    def test_scope_plugin_rejects_stale_integrity_report(self) -> None:
        root = self._plugin_root()
        (root / "plugin/creator-toolchain/README.md").write_text("changed\n", encoding="utf-8")

        findings = validator.validate_plugin_package(root)

        self.assertIn("PACKAGE_INTEGRITY_REPORT", self._ids(findings))

    def test_scope_plugin_requires_version_101(self) -> None:
        root = self._plugin_root()
        manifest_path = root / "plugin/creator-toolchain/.codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = "1.0.0"
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

        findings = validator.validate_plugin_package(root)

        self.assertIn("MANIFEST_VERSION", self._ids(findings))

    def test_scope_plugin_requires_license_parity(self) -> None:
        root = self._plugin_root()
        (root / "plugin/creator-toolchain/LICENSE").write_text("different\n", encoding="utf-8")

        findings = validator.validate_plugin_package(root)

        self.assertIn("LEGAL_PARITY", self._ids(findings))

    def test_scope_all_aggregates_failures(self) -> None:
        findings = validator.validate_all(self.temp_root)

        self.assertEqual({finding.scope for finding in findings}, {"repo", "state", "plugin"})

    def test_invalid_scope_exits_two(self) -> None:
        self.assertEqual(validator.main(["--scope", "invalid"]), 2)


if __name__ == "__main__":
    unittest.main()
