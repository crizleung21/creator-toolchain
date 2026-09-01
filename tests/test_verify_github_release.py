from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify_github_release import ReleaseVerificationError, verify_release


class VerifyGitHubReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name) / "release.json"
        self.release = {
            "tagName": "v1.1.0",
            "isDraft": False,
            "isPrerelease": False,
            "url": "https://github.com/crizleung21/creator-toolchain/releases/tag/v1.1.0",
            "targetCommitish": "a" * 40,
            "assets": [
                {"name": "creator-toolchain-v1.1.0.zip"},
                {"name": "creator-toolchain-v1.1.0.zip.sha256"},
            ],
        }

    def _write(self) -> None:
        self.path.write_text(json.dumps(self.release) + "\n", encoding="utf-8")

    def test_stable_release_with_required_assets_passes(self) -> None:
        self._write()

        result = verify_release(self.path, tag="v1.1.0", version="1.1.0")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["tag"], "v1.1.0")
        self.assertEqual(len(result["asset_names"]), 2)

    def test_draft_or_prerelease_is_rejected(self) -> None:
        for field in ("isDraft", "isPrerelease"):
            with self.subTest(field=field):
                self.release[field] = True
                self._write()
                with self.assertRaises(ReleaseVerificationError):
                    verify_release(self.path, tag="v1.1.0", version="1.1.0")
                self.release[field] = False

    def test_missing_checksum_asset_is_rejected(self) -> None:
        self.release["assets"] = [{"name": "creator-toolchain-v1.1.0.zip"}]
        self._write()

        with self.assertRaises(ReleaseVerificationError):
            verify_release(self.path, tag="v1.1.0", version="1.1.0")

    def test_wrong_tag_is_rejected(self) -> None:
        self.release["tagName"] = "v1.0.1"
        self._write()

        with self.assertRaises(ReleaseVerificationError):
            verify_release(self.path, tag="v1.1.0", version="1.1.0")


if __name__ == "__main__":
    unittest.main()
