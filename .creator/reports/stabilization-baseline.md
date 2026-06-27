# Creator Toolchain Stabilization Baseline

## Capture

- captured_at: `2026-06-27T14:44:38+0800`
- baseline_branch: `main`
- work_branch: `codex/stabilize-creator-toolchain`
- baseline_commit: `38a57bb55aee7f7c1dc10aeb1813e3591a116bdc`
- remote: `https://github.com/crizleung21/creator-toolchain.git`
- status: `DONE_WITH_CONCERNS`

## Governance Input Hashes

| Input | SHA-256 |
|---|---|
| ChristopherKahler toolchain map | `89d55a444ac5aff7eefb49c036592555ad4edfca2aca28fdcfb920887b3ccbb2` |
| Implementation plan v0.4.1 | `42ce35404faee56e552ef9f1abc0aec0ed90ba26403773e58f5f733a8ba8573a` |
| Source traceability audit | `8763426f14a901d4f39e40933ba601939167b99bd9e5815b0241bde3c20ccc1c` |
| Approved reviewed plan | `5c3a0983cae7ccaf8b65e33a17fee894d8d391e6a772006d9fa87cd480f93f59` |

## Upstream HEAD Verification

Verified with `git ls-remote` on 2026-06-27. All six HEAD values match the source map snapshot.

| Repository | HEAD |
|---|---|
| `ChristopherKahler/paul` | `960b05c0b8e1f876f49674a700c9a087afebb8ac` |
| `ChristopherKahler/seed` | `1183a1e43df06171a4d91719f28e22ff0b28e3f4` |
| `ChristopherKahler/base` | `85f861c0a1efc90504f1b29e932b7145336c067e` |
| `ChristopherKahler/carl` | `479319fc6da1176aa2f36203d42c7e0e43ad1c94` |
| `ChristopherKahler/skillsmith` | `7a9ff943ae8905cdbaf858436f8da961ebc2ebfe` |
| `ChristopherKahler/aegis` | `73a64618a6f74d6bf74b0ad535197f196be73fd4` |

## Worktree Inventory

The baseline contained untracked repo-local skills, `.creator/` state, `.gitignore`, marketplace metadata, codebase-memory artifacts, and the plugin manifest. No stash, reset, clean, or checkout-based recovery was used.

Tracked placeholder count: `19`.

Physical `.DS_Store` count at execution start: `8`. This exceeds the reviewed-plan estimate of five because Finder regenerated additional files after review. The generated inventory, not the estimate, controls cleanup.

## Privacy Classification

| Surface | Baseline class | Planned treatment |
|---|---|---|
| `.creator/operator.json` | private | preserve current values in ignored `operator.local.json`; track a generic template surface |
| `.creator/entities.json` | private, empty | track sanitized empty template surface |
| `.creator/psmm.json` | private, empty | track sanitized empty template surface |
| `.creator/backlog.json` | local private | sanitize and track repository workflow state |
| `.creator/projects.json` | local private | sanitize and track repository workflow state |
| `.creator/decisions.json` | local private | sanitize and track repository architecture decisions |
| `.creator/rules.json` | local private | sanitize and track repository rule contract |
| `.creator/state.json` | local private | sanitize and track repository state contract |
| `.creator/workspace.json` | publishable template | track after pointer repair |

## Baseline Validation

`python3 scripts/validate_creator_toolchain.py` exited `1` because three governance files were absent and eight `.DS_Store` files were present.

The bundled plugin validator exited `0` for `plugin/creator-toolchain`.

All seven authoritative repo-local skills exited `0` under the bundled `quick_validate.py` check.

## Constraints Carried Forward

- Do not package `.creator/`, `.agents/`, research inputs, caches, or OS metadata.
- Do not treat the expected baseline validator failure as a release pass.
- Do not stage private local overlays.
- Do not produce release evidence before the package is frozen.
