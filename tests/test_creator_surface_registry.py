from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.creator_surface_registry import EXPECTED_PATHS, SurfaceRegistryError, load_surface_registry, registry_summary
from scripts.materialize_surface_registry import synchronize

ROOT = Path(__file__).resolve().parents[1]


class CreatorSurfaceRegistryTests(unittest.TestCase):
    def test_registry_declares_exact_canonical_surfaces(self) -> None:
        registry = load_surface_registry(ROOT)
        self.assertEqual(tuple(registry), EXPECTED_PATHS)
        self.assertEqual(registry[".creator/rules.json"]["owner_skill"], "creator-rule-router")
        self.assertEqual(sum(item["owner_skill"] == "creator-workspace-manager" for item in registry.values()), 9)

    def test_registry_summary_is_machine_readable(self) -> None:
        summary = registry_summary(ROOT)
        self.assertEqual(summary["schema_version"], "1.0.0")
        self.assertEqual(summary["state_schema_version"], "0.4.0")
        self.assertEqual(summary["surface_count"], 10)
        self.assertEqual([item["path"] for item in summary["surfaces"]], list(EXPECTED_PATHS))

    def test_materialized_outputs_are_current(self) -> None:
        self.assertEqual(synchronize(ROOT, write=False), [])

    def test_duplicate_surface_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            value = json.loads((ROOT / "config/surface-registry.json").read_text(encoding="utf-8"))
            value["surfaces"][1]["surface_id"] = value["surfaces"][0]["surface_id"]
            (root / "config/surface-registry.json").write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(SurfaceRegistryError):
                load_surface_registry(root)


if __name__ == "__main__":
    unittest.main()
