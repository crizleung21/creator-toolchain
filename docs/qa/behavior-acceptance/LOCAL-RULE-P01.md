# Rule Preflight

## Matched Domains

| Domain | Reason | Rules Loaded |
|---|---|---:|
| `GLOBAL` | Always eligible | 1 |
| `creator-toolchain` | Triggered by “plugin” and “package” | 1 |

## Selected Rules

| Rule ID | Severity | Reason |
|---|---|---|
| `GLOBAL-002` | High | Prevents private state, caches, environment files, and build artifacts from entering the package |
| `CT-001` | High | Requires authoritative skill-mirror parity and exact package integrity |

## Non-Loaded Candidates

| Candidate | Reason excluded |
|---|---|
| `GLOBAL-001` | Concerns `.creator/*.json` mutation; this preflight is read-only and requests no state change |
| `zh-Hant` rules | No zh-Hant domain or rules exist in the current [rule registry](/Users/criz/Desktop/creator-toolchain-rebaseline/.creator/rules.json), so none can be loaded |
| Unrelated domains | No other domains are registered; rules must not be invented or loaded speculatively |

## Conflict Warnings

No conflict exists between the selected rules. Accepted decisions `DEC-002` and `DEC-003` reinforce mirror parity and exact package inventory.

There is a coverage gap: the router advertises zh-Hant routing, but the registry currently provides no zh-Hant domain.

## Next Action

Apply `GLOBAL-002` and `CT-001`, ensure all Chinese package content consistently uses Traditional Chinese, then run the repository’s four packaging validation commands. Define and approve a zh-Hant domain before relying on enforceable terminology or script-specific rules. No state was changed.