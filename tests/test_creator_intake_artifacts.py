from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.creator_intake_artifacts import ARTIFACT_PATHS, IntakeError, create_intake_package, inspect_intake_package
from scripts.creator_ledger import read_events

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = "2026-07-18T00:00:00Z"


def complete_request():
    return {
        "title": "Creator Asset Naming Checker",
        "project_type": "utility",
        "goal": "Create a deterministic naming checker.",
        "context": "A reusable creator workflow needs safe asset names.",
        "scope": ["Manifest input", "Validation report"],
        "out_of_scope": ["Automatic renaming"],
        "acceptance_criteria": [
            {"id": "AC-1", "title": "Duplicates", "given": "duplicates", "when": "checked", "then": "duplicates are listed"},
            {"id": "AC-2", "title": "Invalid", "given": "invalid names", "when": "checked", "then": "rules are listed"},
            {"id": "AC-3", "title": "Repeatable", "given": "same input", "when": "run twice", "then": "output matches"},
        ],
        "risks": ["Unsafe paths"],
    }


class CreatorIntakeArtifactTests(unittest.TestCase):
    def test_create_writes_exact_canonical_artifact_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = create_intake_package(root, complete_request(), timestamp=TIMESTAMP, registry_root=ROOT)
            plan_dir = Path(result["plan_dir"])
            self.assertEqual({path.name for path in plan_dir.iterdir()}, set(ARTIFACT_PATHS.values()))
            project = json.loads((plan_dir / "project.json").read_text(encoding="utf-8"))
            for filename in ("INTAKE-STATE.md", "PLANNING.md", "DECISIONS.md", "HANDOFF.md"):
                self.assertIn(project["project_id"], (plan_dir / filename).read_text(encoding="utf-8"))
            self.assertEqual(project["stage"], "planned")
            self.assertEqual(project["quality_gate_result"], "pass")

    def test_creation_is_transactional_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = create_intake_package(root, complete_request(), timestamp=TIMESTAMP, registry_root=ROOT)
            project_path = Path(first["plan_dir"]) / "project.json"
            before = project_path.read_bytes()
            with self.assertRaises(IntakeError):
                create_intake_package(root, complete_request(), timestamp=TIMESTAMP, registry_root=ROOT)
            self.assertEqual(project_path.read_bytes(), before)
            self.assertFalse(any(path.name.startswith(".creator-asset-naming-checker") for path in project_path.parent.parent.iterdir()))

    def test_ledger_records_intake_and_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = create_intake_package(root, complete_request(), timestamp=TIMESTAMP, registry_root=ROOT)
            events = read_events(Path(result["plan_dir"]) / "activity_ledger.jsonl")
            self.assertEqual([event["sequence"] for event in events], [1, 2])
            self.assertEqual([event["phase"] for event in events], ["intake", "gate"])
            self.assertEqual(len({event["event_id"] for event in events}), 2)

    def test_status_resumes_from_existing_package_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            created = create_intake_package(root, complete_request(), timestamp=TIMESTAMP, registry_root=ROOT)
            plan_dir = Path(created["plan_dir"])
            before = {path.name: path.read_bytes() for path in plan_dir.iterdir()}
            status = inspect_intake_package(root, created["slug"])
            after = {path.name: path.read_bytes() for path in plan_dir.iterdir()}
            self.assertEqual(status["result"], "pass")
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
