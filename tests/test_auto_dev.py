"""Safety and task selection tests for VAILABLE automation."""
import json
from pathlib import Path
import unittest
from scripts.auto_dev import next_task, safe_path, GateError, read_json, ROOT


class TaskSelectionTests(unittest.TestCase):
    def setUp(self):
        self.roadmap = read_json(ROOT / "engineering/ROADMAP.json")

    def test_starts_at_vai_001(self):
        self.assertEqual(next_task(self.roadmap, {"completed_tasks": []})["id"], "VAI-001")

    def test_dependency_unlocks_next(self):
        self.assertEqual(next_task(self.roadmap, {"completed_tasks": ["VAI-001"]})["id"], "VAI-002")

    def test_all_complete(self):
        self.assertIsNone(next_task(self.roadmap, {"completed_tasks": [t["id"] for t in self.roadmap["tasks"]]}))

    def test_unknown_progress_rejected(self):
        with self.assertRaises(GateError):
            next_task(self.roadmap, {"completed_tasks": ["FAKE-000"]})

    def test_dependency_cycle_rejected(self):
        changed = json.loads(json.dumps(self.roadmap))
        changed["tasks"][0]["depends_on"] = ["VAI-012"]
        with self.assertRaises(GateError):
            next_task(changed, {"completed_tasks": []})


class WriteScopeTests(unittest.TestCase):
    def test_normal_product_file_allowed(self):
        self.assertTrue(safe_path("apps/web/app/page.tsx"))
        self.assertTrue(safe_path("services/api/app/main.py"))
        self.assertTrue(safe_path("tests/test_merge.py"))

    def test_protected_files_rejected(self):
        for path in ["scripts/auto_dev.py", "engineering/ROADMAP.json", ".github/workflows/ci.yml",
                     "engineering/AUTONOMY_POLICY.md", "docs/security/THREAT_MODEL.md"]:
            with self.subTest(path=path):
                self.assertFalse(safe_path(path))

    def test_secrets_and_traversal_rejected(self):
        for path in ["../outside.txt", "apps/../x.py", "/tmp/foo.py", "apps/web/.env",
                     "apps/web/.env.production", "docs/secret.txt", "services/api/token.json",
                     "services/api/cert.key", ".vailable/runs/output.log"]:
            with self.subTest(path=path):
                self.assertFalse(safe_path(path))


if __name__ == "__main__":
    unittest.main()
