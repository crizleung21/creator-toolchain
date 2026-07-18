from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.creator_execution_closure import close_execution, recover_execution
from scripts.creator_execution_lifecycle import (
    ExecutionLifecycleError,
    initialize_execution,
    record_verification,
    transition_execution,
    transition_task,
)
from scripts.creator_ledger import read_events

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = "2026-07-18T06:00:00Z"
PROJECT_ID = "PROJECT-BBBBBBBB"


class CreatorExecutionClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.handoff_relative = f".creator/handoffs/{PROJECT_ID}.json"
        plan_dir = self.root / ".creator/plans/demo"
        plan_dir.mkdir(parents=True)
        artifact_paths = []
        for name in (
            "project.json",
            "activity_ledger.jsonl",
            "INTAKE-STATE.md",
            "PLANNING.md",
            "DECISIONS.md",
            "OPEN-QUESTIONS.md",
            "HANDOFF.md",
        ):
            path = plan_dir / name
            path.write_text("{}\n" if name.endswith(".json") else f"# {name}\n", encoding="utf-8")
            artifact_paths.append(path.relative_to(self.root).as_posix())
        handoff_path = self.root / self.handoff_relative
        handoff_path.parent.mkdir(parents=True)
        handoff = {
            "schema_version": "1.0.0",
            "project_id": PROJECT_ID,
            "source_plan": ".creator/plans/demo/PLANNING.md",
            "target_skill": "creator-execution-cycle",
            "quality_gate_result": "pass",
            "approval_status": "approved",
            "approval_decision": "handoff-to-execution",
            "approved_by": "tester",
            "approved_at": TIMESTAMP,
            "artifact_paths": artifact_paths,
            "open_questions": [],
            "generated_at": TIMESTAMP,
        }
        handoff_path.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
        self.tasks = [
            {
                "title": "Implement deterministic checker",
                "acceptance_criteria": [
                    "Given valid input, when checked, then a deterministic report is produced."
                ],
                "affected_files": ["src/checker.py"],
                "verification": {
                    "method": "command",
                    "command": "python3 -m unittest",
                    "expected_result": "Exit code 0 and deterministic output.",
                },
            }
        ]
        projects = self.root / ".creator/projects.json"
        projects.write_text('{"sentinel":"unchanged"}\n', encoding="utf-8")

    def _execution_dir(self) -> Path:
        return self.root / ".creator/executions" / PROJECT_ID

    def _initialize(self) -> str:
        initialize_execution(
            self.root,
            self.handoff_relative,
            self.tasks,
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        tasks = json.loads((self._execution_dir() / "tasks.json").read_text(encoding="utf-8"))
        return tasks["tasks"][0]["task_id"]

    def _begin_task(self) -> str:
        task_id = self._initialize()
        transition_execution(
            self.root,
            PROJECT_ID,
            "EXECUTING",
            actor="tester",
            reason="begin",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        transition_task(
            self.root,
            PROJECT_ID,
            task_id,
            "EXECUTING",
            actor="tester",
            reason="start task",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        transition_task(
            self.root,
            PROJECT_ID,
            task_id,
            "EXECUTED",
            actor="tester",
            reason="task output complete",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        transition_execution(
            self.root,
            PROJECT_ID,
            "VERIFYING",
            actor="tester",
            reason="verify output",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        return task_id

    def _prepare_reconciling(self) -> tuple[str, Path]:
        task_id = self._begin_task()
        evidence = self.root / "evidence/task.txt"
        evidence.parent.mkdir()
        evidence.write_text("deterministic result\n", encoding="utf-8")
        record_verification(
            self.root,
            PROJECT_ID,
            task_id,
            result="PASS",
            actual_result="Command exited 0.",
            evidence_relative="evidence/task.txt",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        transition_execution(
            self.root,
            PROJECT_ID,
            "RECONCILING",
            actor="tester",
            reason="all tasks verified",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        return task_id, evidence

    def test_close_creates_mandatory_closure_and_staged_proposal(self) -> None:
        task_id, _ = self._prepare_reconciling()
        projects_path = self.root / ".creator/projects.json"
        projects_before = projects_path.read_bytes()
        result = close_execution(
            self.root,
            PROJECT_ID,
            status="DONE",
            actor="tester",
            recommended_next_action="Ask creator-workspace-manager to review the staged proposal.",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "DONE")
        execution_dir = self._execution_dir()
        for name in (
            "RECONCILIATION-001.json",
            "RECONCILIATION-001.md",
            "SUMMARY-001.md",
            "state-update-proposal.json",
        ):
            self.assertTrue((execution_dir / name).is_file(), name)
        proposal = json.loads((execution_dir / "state-update-proposal.json").read_text(encoding="utf-8"))
        self.assertEqual(proposal["status"], "staged")
        self.assertEqual(proposal["owner_skill"], "creator-workspace-manager")
        self.assertEqual(proposal["requested_by"], "creator-execution-cycle")
        self.assertEqual(proposal["verified_tasks"][0]["task_id"], task_id)
        self.assertEqual(projects_path.read_bytes(), projects_before)
        events = read_events(execution_dir / "activity_ledger.jsonl")
        self.assertEqual(events[-1]["status"], "DONE")
        self.assertEqual(
            result["closure"]["recommended_next_action"],
            "Ask creator-workspace-manager to review the staged proposal.",
        )

    def test_close_rejects_stale_evidence_without_writes(self) -> None:
        _, evidence = self._prepare_reconciling()
        evidence.write_text("changed after verification\n", encoding="utf-8")
        before = {
            path.name: path.read_bytes()
            for path in self._execution_dir().iterdir()
            if path.is_file()
        }
        with self.assertRaises(ExecutionLifecycleError):
            close_execution(
                self.root,
                PROJECT_ID,
                status="DONE",
                actor="tester",
                recommended_next_action="Review state proposal.",
                timestamp=TIMESTAMP,
                schema_root=ROOT,
            )
        after = {
            path.name: path.read_bytes()
            for path in self._execution_dir().iterdir()
            if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertFalse((self._execution_dir() / "SUMMARY-001.md").exists())

    def test_done_with_concerns_requires_concern_and_done_rejects_one(self) -> None:
        self._prepare_reconciling()
        with self.assertRaises(ExecutionLifecycleError):
            close_execution(
                self.root,
                PROJECT_ID,
                status="DONE_WITH_CONCERNS",
                actor="tester",
                recommended_next_action="Review concern.",
                concerns=[],
                timestamp=TIMESTAMP,
                schema_root=ROOT,
            )
        with self.assertRaises(ExecutionLifecycleError):
            close_execution(
                self.root,
                PROJECT_ID,
                status="DONE",
                actor="tester",
                recommended_next_action="Review state proposal.",
                concerns=["Residual risk"],
                timestamp=TIMESTAMP,
                schema_root=ROOT,
            )

    def test_failed_verification_recovery_returns_to_executing(self) -> None:
        task_id = self._begin_task()
        evidence = self.root / "evidence/failure.txt"
        evidence.parent.mkdir()
        evidence.write_text("failure details\n", encoding="utf-8")
        record_verification(
            self.root,
            PROJECT_ID,
            task_id,
            result="FAIL",
            actual_result="Command exited 1.",
            evidence_relative="evidence/failure.txt",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        result = recover_execution(
            self.root,
            PROJECT_ID,
            recovery_type="failed-verification",
            actor="tester",
            reason="Fix the failed task and rerun verification.",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "EXECUTING")
        self.assertTrue((self._execution_dir() / "RECOVERY-PLAN.md").is_file())
        tasks = json.loads((self._execution_dir() / "tasks.json").read_text(encoding="utf-8"))
        self.assertEqual(tasks["tasks"][0]["status"], "FAILED")

    def test_scope_creep_recovery_blocks_and_records_artifacts(self) -> None:
        self._initialize()
        transition_execution(
            self.root,
            PROJECT_ID,
            "EXECUTING",
            actor="tester",
            reason="begin",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        result = recover_execution(
            self.root,
            PROJECT_ID,
            recovery_type="scope-creep",
            actor="tester",
            reason="Unplanned deployment work was requested.",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "BLOCKED")
        self.assertTrue((self._execution_dir() / "SCOPE-CREEP.md").is_file())
        self.assertTrue((self._execution_dir() / "BLOCKER.md").is_file())

    def test_incomplete_reconciliation_recovery_is_explicit(self) -> None:
        self._prepare_reconciling()
        result = recover_execution(
            self.root,
            PROJECT_ID,
            recovery_type="incomplete-reconciliation",
            actor="tester",
            reason="Closure generation was interrupted.",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "RECOVERING")
        self.assertTrue((self._execution_dir() / "RECONCILIATION-RECOVERY.md").is_file())
        self.assertTrue((self._execution_dir() / "RECOVERY-PLAN.md").is_file())

    def test_state_divergence_and_orphan_plan_recoveries(self) -> None:
        self._initialize()
        result = recover_execution(
            self.root,
            PROJECT_ID,
            recovery_type="orphan-plan",
            actor="tester",
            reason="Plan exists without execution closure.",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "BLOCKED")
        self.assertTrue((self._execution_dir() / "RECONCILIATION-RECOVERY.md").is_file())
        self.assertTrue((self._execution_dir() / "BLOCKER.md").is_file())

    def test_state_divergence_recovery_records_evidence(self) -> None:
        self._initialize()
        transition_execution(
            self.root,
            PROJECT_ID,
            "EXECUTING",
            actor="tester",
            reason="begin",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        result = recover_execution(
            self.root,
            PROJECT_ID,
            recovery_type="state-divergence",
            actor="tester",
            reason="Repository state no longer matches the accepted plan.",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "RECOVERING")
        self.assertTrue((self._execution_dir() / "STATE-DIVERGENCE.md").is_file())
        self.assertTrue((self._execution_dir() / "RECOVERY-PLAN.md").is_file())

    def test_interrupted_and_blocked_task_recovery_paths(self) -> None:
        task_id = self._initialize()
        transition_execution(
            self.root,
            PROJECT_ID,
            "EXECUTING",
            actor="tester",
            reason="begin",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        result = recover_execution(
            self.root,
            PROJECT_ID,
            recovery_type="interrupted-execution",
            actor="tester",
            reason="Execution process stopped unexpectedly.",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "RECOVERING")

        second_root = self.root / "second"
        second_plan = second_root / ".creator/plans/demo"
        second_plan.mkdir(parents=True)
        artifact_paths = []
        for name in (
            "project.json",
            "activity_ledger.jsonl",
            "INTAKE-STATE.md",
            "PLANNING.md",
            "DECISIONS.md",
            "OPEN-QUESTIONS.md",
            "HANDOFF.md",
        ):
            path = second_plan / name
            path.write_text("{}\n" if name.endswith(".json") else f"# {name}\n", encoding="utf-8")
            artifact_paths.append(path.relative_to(second_root).as_posix())
        handoff_path = second_root / self.handoff_relative
        handoff_path.parent.mkdir(parents=True)
        handoff = {
            "schema_version": "1.0.0",
            "project_id": PROJECT_ID,
            "source_plan": ".creator/plans/demo/PLANNING.md",
            "target_skill": "creator-execution-cycle",
            "quality_gate_result": "pass",
            "approval_status": "approved",
            "approval_decision": "handoff-to-execution",
            "approved_by": "tester",
            "approved_at": TIMESTAMP,
            "artifact_paths": artifact_paths,
            "open_questions": [],
            "generated_at": TIMESTAMP,
        }
        handoff_path.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
        initialize_execution(
            second_root,
            self.handoff_relative,
            self.tasks,
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        tasks = json.loads(
            (second_root / ".creator/executions" / PROJECT_ID / "tasks.json").read_text(
                encoding="utf-8"
            )
        )
        second_task_id = tasks["tasks"][0]["task_id"]
        transition_execution(
            second_root,
            PROJECT_ID,
            "EXECUTING",
            actor="tester",
            reason="begin",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        transition_task(
            second_root,
            PROJECT_ID,
            second_task_id,
            "BLOCKED",
            actor="tester",
            reason="dependency missing",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        result = recover_execution(
            second_root,
            PROJECT_ID,
            recovery_type="blocked-task",
            actor="tester",
            reason="Dependency became available.",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "RECOVERING")
        self.assertTrue(
            (second_root / ".creator/executions" / PROJECT_ID / "BLOCKER.md").is_file()
        )


if __name__ == "__main__":
    unittest.main()
