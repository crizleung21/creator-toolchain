from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.sync_plugin_skills import SKILLS, SyncError, synchronize


class SyncPluginSkillsTests(unittest.TestCase):
    def _source(self, root: Path) -> Path:
        source = root / ".agents/skills"
        for skill in SKILLS:
            path = source / skill
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(f"# {skill}\n", encoding="utf-8")
        return source

    def test_missing_source_root_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(SyncError):
                synchronize(root / "missing", root / "plugin/skills", write=False)

    def test_check_detects_then_write_repairs_mirror(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._source(root)
            destination = root / "plugin/skills"
            destination.mkdir(parents=True)
            self.assertTrue(synchronize(source, destination, write=False))
            self.assertEqual(synchronize(source, destination, write=True), [])
            self.assertEqual(synchronize(source, destination, write=False), [])

    def test_external_source_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._source(root)
            outside = root / "outside.md"
            outside.write_text("secret", encoding="utf-8")
            try:
                (source / SKILLS[0] / "escape.md").symlink_to(outside)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(SyncError):
                synchronize(source, root / "plugin/skills", write=True)

    def test_atomic_failure_restores_previous_mirror_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._source(root)
            destination = root / "plugin/skills"
            synchronize(source, destination, write=True)
            before = {path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()}
            (source / SKILLS[0] / "SKILL.md").write_text("# changed\n", encoding="utf-8")
            def fail(stage: str) -> None:
                if stage == "after_install":
                    raise RuntimeError("injected failure")
            with self.assertRaises(SyncError):
                synchronize(source, destination, write=True, failure_injector=fail)
            after = {path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()}
            self.assertEqual(after, before)

    def test_write_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._source(root)
            destination = root / "plugin/skills"
            synchronize(source, destination, write=True)
            first = {path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()}
            synchronize(source, destination, write=True)
            second = {path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()}
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
