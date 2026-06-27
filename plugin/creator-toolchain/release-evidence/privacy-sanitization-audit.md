# Privacy Sanitization Audit

## Evidence Header

- status: `PASS_WITH_DECLARED_PUBLISHER_IDENTITY`
- tested_at: `2026-06-27T15:12:46+0800`
- tested_commit: `ab507f6807b838bf3b4d04a65ac28e45c7e1cd44`
- scope: `plugin/creator-toolchain/`

## Automated Checks

- no `.creator/`, `.agents/`, `upstream/`, `.env*`, `*.local.json`, cache, or OS artifact;
- no API-key, password, email-address, or user-home-path pattern in package content after evidence normalization;
- no symbolic link escapes the package root;
- generated skills are byte-equivalent to the authoritative source after documented exclusions.

## Manual Review

- state entities, operator preferences, PSMM, decisions, and project data are outside the package;
- test fixture content contains no client or account information;
- prompts contain workflow examples only;
- `author.name` and `interface.developerName` intentionally identify the declared plugin publisher;
- local command evidence uses `$HOME`, `$REPO_ROOT`, `$CODEX_HOME`, or neutral descriptions instead of a personal absolute path.

## Limitation

Path hygiene does not replace content review. Repeat both automated scanning and manual review if skills, prompts, assets, or release evidence change.
