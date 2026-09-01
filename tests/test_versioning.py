from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.versioning import VersionError, check_version_bindings, read_version, synchronize_version, validate_version


class VersioningTests(unittest.TestCase):
    def _root(self, directory: str, version: str = "1.1.0") -> Path:
        root = Path(directory)
        manifest = root / "plugin/creator-toolchain/.codex-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        (root / "VERSION").write_text(version + "\n", encoding="utf-8")
        manifest.write_text(json.dumps({"version": version}) + "\n", encoding="utf-8")
        return root

    def test_current_repository_bindings_match(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(read_version(root), "1.1.0")
        self.assertEqual(check_version_bindings(root), [])

    def test_invalid_version_is_rejected(self) -> None:
        with self.assertRaises(VersionError):
            validate_version("v1.1")

    def test_synchronize_updates_version_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory, "1.0.1")
            self.assertEqual(synchronize_version(root, "1.1.0", write=True), [])
            self.assertEqual(read_version(root), "1.1.0")
            manifest = json.loads((root / "plugin/creator-toolchain/.codex-plugin/plugin.json").read_text())
            self.assertEqual(manifest["version"], "1.1.0")


if __name__ == "__main__":
    unittest.main()
