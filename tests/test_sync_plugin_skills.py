from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from scripts import sync_plugin_skills as sync


class SyncPluginSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.source = self.root / ".agents/skills"
        self.destination = self.root / "plugin/creator-toolchain/skills"
        self._create_equal_trees()

    def _write_skill(self, base: Path, skill: str, marker: str = "same") -> None:
        skill_root = base / skill
        (skill_root / "references").mkdir(parents=True, exist_ok=True)
        (skill_root / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: Test {skill}.\n---\n\n{marker}\n",
            encoding="utf-8",
        )
        (skill_root / "references/guide.md").write_text(marker + "\n", encoding="utf-8")

    def _create_equal_trees(self) -> None:
        for skill in sync.SKILLS:
            self._write_skill(self.source, skill)
            self._write_skill(self.destination, skill)

    def test_check_passes_for_equal_trees(self) -> None:
        self.assertEqual(sync.synchronize(self.source, self.destination, write=False), [])

    def test_check_reports_changed_file(self) -> None:
        path = self.destination / sync.SKILLS[0] / "SKILL.md"
        path.write_text("changed\n", encoding="utf-8")

        findings = sync.synchronize(self.source, self.destination, write=False)

        self.assertTrue(any("different:" in finding for finding in findings))

    def test_check_reports_extra_plugin_file(self) -> None:
        extra = self.destination / sync.SKILLS[0] / "references/extra.md"
        extra.write_text("extra\n", encoding="utf-8")

        findings = sync.synchronize(self.source, self.destination, write=False)

        self.assertTrue(any("extra:" in finding for finding in findings))

    def test_write_copies_all_allowlisted_skills(self) -> None:
        source_file = self.source / sync.SKILLS[0] / "references/guide.md"
        destination_file = self.destination / sync.SKILLS[0] / "references/guide.md"
        source_file.write_text("authoritative\n", encoding="utf-8")
        destination_file.write_text("stale\n", encoding="utf-8")

        findings = sync.synchronize(self.source, self.destination, write=True)

        self.assertEqual(findings, [])
        self.assertEqual(destination_file.read_text(encoding="utf-8"), "authoritative\n")

    def test_write_excludes_generated_junk(self) -> None:
        skill_root = self.source / sync.SKILLS[0]
        (skill_root / ".DS_Store").write_text("junk", encoding="utf-8")
        (skill_root / ".gitkeep").write_text("", encoding="utf-8")
        (skill_root / "cache.pyc").write_bytes(b"junk")
        (skill_root / "Thumbs.db").write_text("junk", encoding="utf-8")
        (skill_root / "build.tar.gz").write_bytes(b"junk")
        (skill_root / ".idea").mkdir()
        (skill_root / ".idea/workspace.xml").write_text("junk", encoding="utf-8")
        (skill_root / ".vscode").mkdir()
        (skill_root / ".vscode/settings.json").write_text("{}\n", encoding="utf-8")

        sync.synchronize(self.source, self.destination, write=True)

        copied = self.destination / sync.SKILLS[0]
        self.assertFalse((copied / ".DS_Store").exists())
        self.assertFalse((copied / ".gitkeep").exists())
        self.assertFalse((copied / "cache.pyc").exists())
        self.assertFalse((copied / "Thumbs.db").exists())
        self.assertFalse((copied / "build.tar.gz").exists())
        self.assertFalse((copied / ".idea").exists())
        self.assertFalse((copied / ".vscode").exists())

    def test_write_removes_stale_generated_skill_directory(self) -> None:
        stale = self.destination / "stale-generated-skill"
        self._write_skill(self.destination, stale.name)

        findings = sync.synchronize(self.source, self.destination, write=True)

        self.assertEqual(findings, [])
        self.assertFalse(stale.exists())

    def test_rejects_unknown_source_skill_directory(self) -> None:
        self._write_skill(self.source, "unknown-skill")

        with self.assertRaisesRegex(sync.SyncError, "unknown source skill"):
            sync.synchronize(self.source, self.destination, write=False)

    def test_rejects_external_symlink(self) -> None:
        outside = self.root / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        link = self.source / sync.SKILLS[0] / "references/external.md"
        os.symlink(outside, link)

        with self.assertRaisesRegex(sync.SyncError, "symlink escapes"):
            sync.synchronize(self.source, self.destination, write=False)

    def test_check_is_read_only(self) -> None:
        path = self.destination / sync.SKILLS[0] / "SKILL.md"
        before = path.stat().st_mtime_ns
        time.sleep(0.001)

        sync.synchronize(self.source, self.destination, write=False)

        self.assertEqual(path.stat().st_mtime_ns, before)


if __name__ == "__main__":
    unittest.main()
