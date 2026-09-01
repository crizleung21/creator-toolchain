from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.versioning import read_version


ROOT = Path(__file__).resolve().parents[1]


class DocumentationContractTests(unittest.TestCase):
    def test_required_phase9_documents_exist(self) -> None:
        required = [
            "CHANGELOG.md",
            "docs/operations/bootstrap.md",
            "docs/operations/execution-lifecycle.md",
            "docs/operations/recovery.md",
            "docs/operations/release.md",
            "docs/operations/troubleshooting.md",
            "docs/releases/v1.1.0.md",
            "docs/implementation/phase-9/PLAN-001.md",
            "docs/implementation/phase-9/RECONCILIATION-001.md",
            "docs/implementation/phase-9/SUMMARY-001.md",
            "docs/implementation/phase-9/GATE-MATRIX.md",
            "docs/implementation/FINAL-RECONCILIATION.md",
            "docs/qa/final-release-status.json",
        ]
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_current_install_docs_use_authoritative_version(self) -> None:
        version = read_version(ROOT)
        for relative in [
            "README.md",
            "plugin/creator-toolchain/README.md",
            "docs/operations/release.md",
            f"docs/releases/v{version}.md",
        ]:
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                self.assertIn(f"v{version}", text)
        plugin_changelog = (ROOT / "plugin/creator-toolchain/CHANGELOG.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(f"## {version}", plugin_changelog)

    def test_active_docs_use_schema_040_and_current_lifecycle_terms(self) -> None:
        active = [
            "README.md",
            "AGENTS.md",
            "docs/architecture/creator-toolchain.md",
            "docs/architecture/state-contract.md",
            "docs/operations/bootstrap.md",
            "docs/operations/execution-lifecycle.md",
            "docs/operations/recovery.md",
        ]
        combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in active)
        self.assertIn("0.4.0", combined)
        self.assertNotIn("Phase 5 plugin workflow", combined)
        self.assertNotIn("Failed Qualify Recovery", combined)
        self.assertNotIn("return to Apply", combined)

    def test_documented_entrypoints_accept_help(self) -> None:
        scripts = [
            "scripts/bootstrap_creator_workspace.py",
            "scripts/creator_execution_lifecycle.py",
            "scripts/creator_execution_closure.py",
            "scripts/migrate_creator_state.py",
            "scripts/creator_health_check.py",
            "scripts/reconcile_creator_state.py",
            "scripts/package_integrity.py",
            "scripts/release_creator_toolchain.py",
            "scripts/finalize_phase9.py",
        ]
        for relative in scripts:
            with self.subTest(script=relative):
                process = subprocess.run(
                    [sys.executable, str(ROOT / relative), "--help"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(process.returncode, 0, process.stderr)

    def test_final_release_status_has_eighteen_unique_gate_ids(self) -> None:
        status = json.loads(
            (ROOT / "docs/qa/final-release-status.json").read_text(encoding="utf-8")
        )
        ids = [item["gate_id"] for item in status["gates"]]
        self.assertEqual(len(ids), 18)
        self.assertEqual(len(set(ids)), 18)
        self.assertEqual(ids, [f"GATE-{index:02d}" for index in range(1, 19)])

    def test_package_docs_preserve_seven_skill_boundary(self) -> None:
        text = (
            (ROOT / "plugin/creator-toolchain/README.md").read_text(encoding="utf-8")
            + (ROOT / "plugin/creator-toolchain/CHANGELOG.md").read_text(encoding="utf-8")
        )
        for skill in [
            "creator-orchestrator",
            "creator-intake-planner",
            "creator-execution-cycle",
            "creator-workspace-manager",
            "creator-rule-router",
            "creator-skill-workbench",
            "creator-evidence-audit",
        ]:
            self.assertIn(skill, text)
        self.assertIn("no eighth core Skill", text)


if __name__ == "__main__":
    unittest.main()
