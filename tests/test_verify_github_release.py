from __future__ import annotations

import unittest

from scripts.verify_github_release import (
    GitHubReleaseVerificationError,
    validate_release_metadata,
)


class VerifyGitHubReleaseTests(unittest.TestCase):
    @staticmethod
    def valid_metadata() -> dict[str, object]:
        return {
            "tagName": "v1.1.0",
            "isDraft": False,
            "isPrerelease": False,
            "targetCommitish": "0123456789abcdef",
            "url": "https://github.com/crizleung21/creator-toolchain/releases/tag/v1.1.0",
            "assets": [
                {"name": "creator-toolchain-v1.1.0.zip"},
                {"name": "creator-toolchain-v1.1.0.zip.sha256"},
            ],
        }

    def test_valid_stable_release_passes(self) -> None:
        result = validate_release_metadata(
            self.valid_metadata(),
            tag="v1.1.0",
            version="1.1.0",
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["tag"], "v1.1.0")
        self.assertEqual(len(result["assets"]), 2)

    def test_missing_checksum_asset_is_rejected(self) -> None:
        value = self.valid_metadata()
        value["assets"] = [{"name": "creator-toolchain-v1.1.0.zip"}]

        with self.assertRaises(GitHubReleaseVerificationError):
            validate_release_metadata(value, tag="v1.1.0", version="1.1.0")

    def test_draft_or_prerelease_is_rejected(self) -> None:
        for field in ("isDraft", "isPrerelease"):
            with self.subTest(field=field):
                value = self.valid_metadata()
                value[field] = True
                with self.assertRaises(GitHubReleaseVerificationError):
                    validate_release_metadata(
                        value,
                        tag="v1.1.0",
                        version="1.1.0",
                    )

    def test_tag_version_mismatch_is_rejected(self) -> None:
        with self.assertRaises(GitHubReleaseVerificationError):
            validate_release_metadata(
                self.valid_metadata(),
                tag="v1.1.1",
                version="1.1.0",
            )


if __name__ == "__main__":
    unittest.main()
