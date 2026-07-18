from __future__ import annotations

import unittest
from pathlib import Path

from scripts.creator_workflow_router import load_routing_config, route_request

ROOT = Path(__file__).resolve().parents[1]


class CreatorWorkflowRouterTests(unittest.TestCase):
    def route(self, text: str):
        return route_request(ROOT, text, schema_root=ROOT)

    def test_raw_idea_routes_to_intake(self) -> None:
        result = self.route("I have a rough concept for a reusable character consistency system.")
        self.assertEqual(result["route_id"], "raw-idea")
        self.assertEqual(result["primary_workflow"], "creator-intake-planner")

    def test_accepted_plan_routes_to_execution(self) -> None:
        result = self.route("Use this approved plan and execute this plan now.")
        self.assertEqual(result["primary_workflow"], "creator-execution-cycle")
        self.assertTrue(result["support_script_available"])

    def test_state_and_rules_route_to_their_owners(self) -> None:
        self.assertEqual(self.route("Run a workspace health check and maintenance review.")["primary_workflow"], "creator-workspace-manager")
        self.assertEqual(self.route("Run rule preflight for this package.")["primary_workflow"], "creator-rule-router")

    def test_skill_audit_precedes_system_audit(self) -> None:
        result = self.route("Audit this skill package and score this skill.")
        self.assertEqual(result["route_id"], "skill-workbench")
        self.assertEqual(result["primary_workflow"], "creator-skill-workbench")

    def test_repository_audit_routes_to_evidence_audit(self) -> None:
        result = self.route("Perform an evidence-first repository audit and produce findings.")
        self.assertEqual(result["primary_workflow"], "creator-evidence-audit")

    def test_plugin_release_has_defined_route_and_explicit_gap(self) -> None:
        result = self.route("Prepare a plugin release for the marketplace.")
        self.assertEqual(result["route_id"], "plugin-release")
        self.assertEqual(result["primary_workflow"], "creator-orchestrator")
        self.assertEqual(result["support_script"], "scripts/release_creator_toolchain.py")
        self.assertFalse(result["support_script_available"])
        self.assertNotIn("Phase 5 plugin workflow", result["handoff_prompt"])
        self.assertTrue(any("release_creator_toolchain.py" in item for item in result["missing_inputs"]))

    def test_exactly_one_fallback_and_unique_priorities(self) -> None:
        config = load_routing_config(ROOT)
        self.assertEqual(sum(item["fallback"] is True for item in config["routes"]), 1)
        self.assertEqual(len({item["priority"] for item in config["routes"]}), len(config["routes"]))


if __name__ == "__main__":
    unittest.main()
