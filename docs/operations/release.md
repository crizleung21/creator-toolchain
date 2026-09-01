# Release Operations

## Stable Release Target

```text
Version: 1.1.0
Tag:     v1.1.0
```

## Preconditions

- Phase reconciliation is `DONE`;
- package inventory is current;
- Behavior Acceptance is `CURRENT` and 34/34 PASS;
- Health is green;
- all 18 gates pass;
- final branch CI passes;
- post-merge `main` validation passes.

## Check

```bash
python3 scripts/release_creator_toolchain.py \
  --root . \
  --check \
  --commit-sha "$(git rev-parse HEAD)"
```

## Build

```bash
rm -rf dist
python3 scripts/release_creator_toolchain.py \
  --root . \
  --build \
  --output-dir dist \
  --commit-sha "$(git rev-parse HEAD)"
```

Expected assets:

```text
dist/creator-toolchain-v1.1.0.zip
dist/creator-toolchain-v1.1.0.zip.sha256
dist/release-evidence.json
```

## Verify Checksum

```bash
shasum -a 256 -c dist/creator-toolchain-v1.1.0.zip.sha256
```

## GitHub Publication

`.github/workflows/publish-release.yml` validates the merged `main` commit, builds the same deterministic assets, creates tag `v1.1.0`, publishes a non-draft non-prerelease GitHub Release, and uploads the ZIP plus SHA-256 sidecar.

The workflow is idempotent: an existing release is verified and not recreated.

## Rollback

Do not move a published tag. When publication fails before the Release is visible, correct the workflow and rerun. When a published asset is invalid, withdraw the Release, preserve evidence of the incident, and publish a new patch version.
