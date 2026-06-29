# Rule Preflight

## Matched Domains

| Domain | Reason | Rules Loaded |
|---|---|---:|
| `GLOBAL` | Always eligible | 1 |
| `ZH_HANT` | Target content uses Traditional Chinese | 2 |
| `PLUGIN_PACKAGING` | Task concerns plugin packaging | 3 |

## Selected Rules

| Rule ID | Severity | Rule | Reason |
|---|---|---|---|
| `GLOBAL.CONTEXT_MINIMUM` | High | Load only relevant domains and rules | Required by the router’s context-budget policy |
| `ZH_HANT.SCRIPT` | High | User-facing Chinese content must use Traditional Chinese consistently | Direct language requirement |
| `ZH_HANT.TERMINOLOGY` | Medium | Keep technical terms and translations consistent across manifests, README, skills, and commands | Prevents mixed terminology |
| `PACKAGING.NO_PRIVATE_STATE` | Critical | Exclude private state and build artifacts | Explicit package trust policy |
| `PACKAGING.SOURCE_EQUIVALENCE` | High | Generated skills must match their authoritative sources | Explicit integrity requirement |
| `PACKAGING.REPRODUCIBLE` | High | Integrity and reproducible-build checks must pass before release | Explicit release gate |

Packaging rules derive from the installed plugin’s [README](/private/tmp/creator-toolchain-codex-plugin-home/plugins/cache/creator-toolchain/creator-toolchain/1.0.1/README.md).

## Non-Loaded Candidate Rules

| Candidate | Reason Not Loaded |
|---|---|
| `SLIDE_DECK` | Mentioned only by [fixture.md](/tmp/creator-toolchain-behavior-workspace/fixture.md); unrelated to plugin packaging |
| `CHARACTER_IMAGE` | Fixture subject matter, not packaging behavior |
| `CREATOR_PRODUCTION` | No image, video, slide, or content-production execution requested |
| `CODING` | No implementation or source modification requested |
| `EXECUTION_CYCLE` | This is preflight only; no approved implementation plan is being executed |
| `SAFETY` | No elevated-risk operation or content was identified |
| `PACKAGING.NO_HOOKS_MCP_APPS` | Excluded as package-specific unless the target is explicitly the Creator Toolchain package |
| Long examples and inactive rules | Excluded under the context-budget rule |

## Conflict Warnings

No conflict exists among the selected rules. No workspace rule registry or decision log is present, so canonical rule IDs and historical conflict references could not be audited.

## Next Action

Apply these rules when packaging begins. Before release, confirm whether the target is the Creator Toolchain plugin; that determines whether its prohibition on hooks, MCP servers, and app integrations applies.