from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.package_integrity import (
    build_integrity_report,
    check_integrity_report,
    file_sha256,
    payload_sha256,
)
from scripts.sync_plugin_skills import SKILLS


class PackageIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.package_root = self.root / "plugin/creator-toolchain"
        self.source_root = self.root / ".agents/skills"
        (self.package_root / ".codex-plugin").mkdir(parents=True)
        (self.package_root / "skills").mkdir()
        (self.package_root / ".codex-plugin/plugin.json").write_text(
            json.dumps({"name": "creator-toolchain", "version": "1.0.1"}) + "\n",
            encoding="utf-8",
        )
        for name in ("README.md", "CHANGELOG.md", "LICENSE"):
            (self.package_root / name).write_text(f"{name}\n", encoding="utf-8")
        for skill in SKILLS:
            source = self.source_root / skill
            plugin = self.package_root / "skills" / skill
            source.mkdir(parents=True)
            plugin.mkdir(parents=True)
            content = f"---\nname: {skill}\ndescription: test\n---\n"
            (source / "SKILL.md").write_text(content, encoding="utf-8")
            (plugin / "SKILL.md").write_text(content, encoding="utf-8")

    @staticmethod
    def _finding_ids(report: dict[str, object]) -> set[str]:
        findings = report.get("findings", [])
        return {
            item["check_id"]
            for item in findings
            if isinstance(item, dict) and isinstance(item.get("check_id"), str)
        }

    def test_current_package_passes_exact_allowlist(self) -> None:
        report = build_integrity_report(self.root, self.package_root)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["package_version"], "1.0.1")
        self.assertEqual(report["file_count"], len(report["files"]))
        self.assertEqual(report["mirror_status"], "PASS")
        self.assertEqual(report["findings"], [])

    def test_unknown_top_level_file_is_rejected(self) -> None:
        (self.package_root / "unexpected.md").write_text("unexpected\n", encoding="utf-8")

        report = build_integrity_report(self.root, self.package_root)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("UNEXPECTED_PATH", self._finding_ids(report))

    def test_unknown_skill_file_is_rejected_by_mirror_parity(self) -> None:
        extra = self.package_root / "skills" / SKILLS[0] / "extra.md"
        extra.write_text("extra\n", encoding="utf-8")

        report = build_integrity_report(self.root, self.package_root)

        self.assertEqual(report["mirror_status"], "FAIL")
        self.assertIn("MIRROR_PARITY", self._finding_ids(report))

    def test_missing_required_file_is_rejected(self) -> None:
        (self.package_root / "README.md").unlink()

        report = build_integrity_report(self.root, self.package_root)

        self.assertIn("MISSING_REQUIRED", self._finding_ids(report))

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_symlink_is_rejected_even_when_internal(self) -> None:
        os.symlink("README.md", self.package_root / "README.link")

        report = build_integrity_report(self.root, self.package_root)

        self.assertIn("SYMLINK", self._finding_ids(report))

    def test_private_state_is_rejected(self) -> None:
        private = self.package_root / ".creator/state.json"
        private.parent.mkdir()
        private.write_text("{}\n", encoding="utf-8")

        report = build_integrity_report(self.root, self.package_root)

        self.assertIn("FORBIDDEN_PATH", self._finding_ids(report))

    def test_environment_file_is_rejected(self) -> None:
        (self.package_root / ".env.local").write_text("SECRET=value\n", encoding="utf-8")

        report = build_integrity_report(self.root, self.package_root)

        self.assertIn("FORBIDDEN_PATH", self._finding_ids(report))

    def test_zip_inside_package_is_rejected(self) -> None:
        (self.package_root / "payload.zip").write_bytes(b"zip")

        report = build_integrity_report(self.root, self.package_root)

        self.assertIn("FORBIDDEN_PATH", self._finding_ids(report))

    def test_editor_metadata_from_source_is_rejected(self) -> None:
        for root in (
            self.source_root / SKILLS[0],
            self.package_root / "skills" / SKILLS[0],
        ):
            path = root / ".idea/workspace.xml"
            path.parent.mkdir()
            path.write_text("editor metadata\n", encoding="utf-8")

        report = build_integrity_report(self.root, self.package_root)

        self.assertIn("FORBIDDEN_PATH", self._finding_ids(report))

    def test_build_archive_from_source_is_rejected(self) -> None:
        for root in (
            self.source_root / SKILLS[0],
            self.package_root / "skills" / SKILLS[0],
        ):
            (root / "build.tar.gz").write_bytes(b"archive")

        report = build_integrity_report(self.root, self.package_root)

        self.assertIn("FORBIDDEN_PATH", self._finding_ids(report))

    def test_report_is_deterministic(self) -> None:
        first = build_integrity_report(self.root, self.package_root)
        second = build_integrity_report(self.root, self.package_root)

        self.assertEqual(first, second)

    def test_stale_report_is_rejected(self) -> None:
        report_path = self.root / "report.json"
        report = build_integrity_report(self.root, self.package_root)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (self.package_root / "README.md").write_text("changed\n", encoding="utf-8")

        findings = check_integrity_report(self.root, self.package_root, report_path)

        self.assertTrue(findings)
        self.assertTrue(any("stale" in finding.lower() for finding in findings))

    def test_payload_hash_changes_when_file_bytes_change(self) -> None:
        file_path = self.package_root / "README.md"
        files = [file_path]
        before = payload_sha256(files, self.package_root)
        file_path.write_text("changed\n", encoding="utf-8")

        self.assertNotEqual(before, payload_sha256(files, self.package_root))

    def test_payload_hash_changes_when_relative_path_changes(self) -> None:
        file_path = self.package_root / "README.md"
        before = payload_sha256([file_path], self.package_root)
        renamed = self.package_root / "RENAMED.md"
        file_path.rename(renamed)

        self.assertNotEqual(before, payload_sha256([renamed], self.package_root))

    def test_file_sha256_matches_known_digest(self) -> None:
        file_path = self.root / "value.txt"
        file_path.write_bytes(b"abc")

        self.assertEqual(
            file_sha256(file_path),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )


if __name__ == "__main__":
    unittest.main()
