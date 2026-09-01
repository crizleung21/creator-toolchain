from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_plugin_package import build_plugin_archive
from scripts.release_creator_toolchain import ReleaseError, clean_install_and_discover
from scripts.sync_plugin_skills import SKILLS
from scripts.versioning import read_version

ROOT = Path(__file__).resolve().parents[1]


class ReleaseCreatorToolchainTests(unittest.TestCase):
    def test_clean_install_discovers_exactly_seven_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "creator-toolchain.zip"
            build_plugin_archive(ROOT, ROOT / "plugin/creator-toolchain", archive)
            self.assertEqual(clean_install_and_discover(archive, read_version(ROOT)), sorted(SKILLS))

    def test_clean_install_rejects_wrong_expected_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "creator-toolchain.zip"
            build_plugin_archive(ROOT, ROOT / "plugin/creator-toolchain", archive)
            with self.assertRaises(ReleaseError):
                clean_install_and_discover(archive, "0.0.0")

    def test_release_schema_asset_exists(self) -> None:
        schema = json.loads((ROOT / "schemas/qa/release-evidence.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["status"]["const"], "PASS")
        self.assertIn("clean_install", schema["properties"]["gates"]["required"])
        self.assertIn("skill_discovery", schema["properties"]["gates"]["required"])


if __name__ == "__main__":
    unittest.main()
