from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/publish-release.yml"


class PublishReleaseWorkflowTests(unittest.TestCase):
    def test_checksum_sidecar_is_verified_from_dist_directory(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("cd dist", text)
        self.assertIn(
            'sha256sum -c "creator-toolchain-v${VERSION}.zip.sha256"',
            text,
        )
        self.assertNotIn(
            'sha256sum -c "dist/creator-toolchain-v${VERSION}.zip.sha256"',
            text,
        )

    def test_release_uploads_zip_and_checksum_assets(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('"dist/creator-toolchain-v${VERSION}.zip#', text)
        self.assertIn('"dist/creator-toolchain-v${VERSION}.zip.sha256#', text)
        self.assertIn('--notes-file "docs/releases/${TAG}.md"', text)
        self.assertIn("--latest", text)

    def test_release_metadata_uses_standalone_verifier_without_nested_heredoc(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertGreaterEqual(text.count("scripts/verify_github_release.py"), 2)
        self.assertNotIn('python3 - "${TAG}" "${VERSION}" <<', text)
        self.assertIn('git rev-list -n 1 "${TAG}"', text)
        self.assertIn('test "${TAG_COMMIT}" = "${GITHUB_SHA}"', text)


if __name__ == "__main__":
    unittest.main()
