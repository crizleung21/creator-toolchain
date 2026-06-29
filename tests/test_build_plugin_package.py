from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.build_plugin_package import build_plugin_package
from scripts.sync_plugin_skills import SKILLS


class BuildPluginPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        package_root = self.root / "plugin/creator-toolchain"
        source_root = self.root / ".agents/skills"
        (package_root / ".codex-plugin").mkdir(parents=True)
        (package_root / "skills").mkdir()
        (package_root / ".codex-plugin/plugin.json").write_text(
            json.dumps({"name": "creator-toolchain", "version": "1.0.1"}) + "\n",
            encoding="utf-8",
        )
        for name in ("README.md", "CHANGELOG.md", "LICENSE"):
            (package_root / name).write_text(f"{name}\n", encoding="utf-8")
        for skill in SKILLS:
            source = source_root / skill
            plugin = package_root / "skills" / skill
            source.mkdir(parents=True)
            plugin.mkdir(parents=True)
            content = f"---\nname: {skill}\ndescription: test\n---\n"
            (source / "SKILL.md").write_text(content, encoding="utf-8")
            (plugin / "SKILL.md").write_text(content, encoding="utf-8")

    def test_two_package_builds_have_identical_sha256(self) -> None:
        first = self.root / "first.zip"
        second = self.root / "second.zip"

        first_result = build_plugin_package(self.root, first)
        second_result = build_plugin_package(self.root, second)

        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(first_result["sha256"], second_result["sha256"])
        self.assertEqual(first_result["file_count"], second_result["file_count"])

    def test_zip_has_sorted_paths_fixed_timestamps_and_0644_modes(self) -> None:
        output = self.root / "package.zip"

        build_plugin_package(self.root, output)

        with zipfile.ZipFile(output) as archive:
            infos = archive.infolist()
        names = [info.filename for info in infos]
        self.assertEqual(names, sorted(names))
        self.assertTrue(all(name.startswith("creator-toolchain/") for name in names))
        self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in infos))
        self.assertTrue(all((info.external_attr >> 16) & 0o777 == 0o644 for info in infos))

    def test_builder_writes_matching_sha256_sidecar(self) -> None:
        output = self.root / "package.zip"

        result = build_plugin_package(self.root, output)

        sidecar = output.with_name(output.name + ".sha256")
        self.assertEqual(sidecar.read_text(encoding="utf-8"), f"{result['sha256']}  {output.name}\n")


if __name__ == "__main__":
    unittest.main()
