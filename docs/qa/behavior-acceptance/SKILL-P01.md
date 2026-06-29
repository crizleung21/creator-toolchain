## Discovered skill

`creator-subtitle-qa`

A standalone QA skill for validating creator-facing subtitle files before publishing. No existing subtitle or caption skill conflicts with this name.

Primary scope:

- SRT and WebVTT structural validation
- Timing, overlap, duration, and ordering checks
- Reading-speed and line-length checks
- Text consistency and optional transcript comparison
- Actionable QA report
- Corrected subtitle output only when explicitly requested

Out of scope: transcription, translation, video editing, subtitle burn-in, and subjective creative rewriting.

## Skill spec

```yaml
skill_name: creator-subtitle-qa

description: >
  Audit SRT and WebVTT creator subtitles for syntax, timing, readability,
  text consistency, and optional transcript fidelity. Use for subtitle QA,
  caption review, timed-text validation, overlap detection, reading-speed
  checks, or pre-publish subtitle verification. Do not use for transcription,
  translation, video editing, burn-in, or unrestricted copy rewriting.

tier: standalone

primary_trigger:
  - audit or QA a subtitle file before publication

secondary_triggers:
  - validate SRT or WebVTT
  - check subtitle timing or overlaps
  - check subtitle reading speed
  - compare captions with a supplied transcript
  - produce a corrected subtitle file

not_for:
  - generating subtitles from audio or video
  - translating subtitles
  - burning captions into video
  - editing video timelines
  - evaluating unsupported ASS/SSA styling
  - rewriting dialogue without explicit authorization

inputs:
  required:
    - subtitle file in SRT or WebVTT format
  optional:
    - source transcript
    - video duration
    - frame rate
    - language or locale
    - creator style guide
    - reading-speed threshold
    - maximum characters per line
    - correction authorization

outputs:
  - machine-readable issue inventory
  - human-readable QA report
  - severity and cue references for every finding
  - corrected subtitle file when explicitly requested
  - unresolved ambiguities and assumptions

folders:
  - references/workflows
  - references/frameworks
  - references/checklists
  - assets/templates
  - scripts
  - tests/fixtures

references:
  - references/workflows/audit-subtitles.md
  - references/frameworks/subtitle-quality-model.md
  - references/checklists/subtitle-qa.md

assets:
  - assets/templates/subtitle-qa-report.md
  - assets/templates/subtitle-issues.json

scripts:
  - scripts/validate_subtitles.py

state_surfaces:
  reads:
    - optional project subtitle conventions
    - optional creator language and style rules
  writes:
    - none by default
    - corrected subtitle and QA-report artifacts only when requested
  mutation_policy:
    - never overwrite the source subtitle
    - preserve cue order and wording unless correction is authorized
    - record every automated correction

rule_domains:
  - creator-production
  - subtitle-accessibility
  - locale-specific-writing
  - zh-Hant-writing-when-applicable

acceptance_tests:
  - >
    Given a malformed SRT timestamp, when the skill audits the file,
    then it reports the cue, malformed value, severity, and suggested repair.
  - >
    Given overlapping or non-monotonic cues, when timing checks run,
    then every conflict identifies both affected cue numbers.
  - >
    Given configured reading-speed and line-length limits, when a cue exceeds
    either limit, then the report includes measured and allowed values.
  - >
    Given a source transcript, when subtitle text materially diverges,
    then the report identifies the mismatch without inventing replacement text.
  - >
    Given correction authorization, when safe deterministic fixes are applied,
    then a new file is produced and every change appears in a correction log.
  - >
    Given no correction authorization, when defects are found,
    then the source and workspace state remain unchanged.
  - >
    Given an unsupported format, when auditing begins,
    then the skill stops with a clear capability boundary.

owner: creator-toolchain
phase_added: proposed
```

## Scaffold

```text
creator-subtitle-qa/
├── SKILL.md
├── references/
│   ├── workflows/
│   │   └── audit-subtitles.md
│   ├── frameworks/
│   │   └── subtitle-quality-model.md
│   └── checklists/
│       └── subtitle-qa.md
├── assets/
│   └── templates/
│       ├── subtitle-qa-report.md
│       └── subtitle-issues.json
├── scripts/
│   └── validate_subtitles.py
└── tests/
    └── fixtures/
        ├── valid.srt
        ├── malformed.srt
        ├── overlapping.vtt
        └── excessive-reading-speed.srt
```

`SKILL.md` routes the audit workflow and declares mutation boundaries. The validator handles deterministic parsing and metrics; framework and checklist files define quality rules; templates stabilize report formats; fixtures prove the acceptance tests.

Projected compliance: **94/100 — compliant**. The workspace is read-only, so this scaffold was specified but not created.