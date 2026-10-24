"""Safety and task selection tests for VAILABLE automation."""
import json
from pathlib import Path
import unittest
from scripts.auto_dev import next_task, safe_path, GateError, read_json, ROOT, vai001_artifacts
from scripts.verify import discover_api_tests, web_dependencies_required
from tempfile import TemporaryDirectory


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


class WebManifestTests(unittest.TestCase):
    def test_dependency_free_package_does_not_require_node_modules(self):
        with TemporaryDirectory() as tmp:
            web = Path(tmp)
            (web / "package.json").write_text(json.dumps({
                "name": "vailable-web", "private": True,
                "scripts": {"test": "node --test test/*.test.mjs"},
            }))
            self.assertFalse(web_dependencies_required(web))

    def test_dependency_based_package_needs_node_modules(self):
        with TemporaryDirectory() as tmp:
            web = Path(tmp)
            (web / "package.json").write_text(json.dumps({
                "name": "vailable-web", "private": True,
                "scripts": {"test": "vitest run"},
                "devDependencies": {"vitest": "^3.0.0"},
            }))
            self.assertTrue(web_dependencies_required(web))

    def test_rejects_empty_test_command(self):
        with TemporaryDirectory() as tmp:
            web = Path(tmp)
            (web / "package.json").write_text('{"name":"vailable-web","scripts":{}}')
            with self.assertRaisesRegex(SystemExit, "test command"):
                web_dependencies_required(web)

    def test_rejects_invalid_json(self):
        with TemporaryDirectory() as tmp:
            web = Path(tmp)
            (web / "package.json").write_text('{')
            with self.assertRaisesRegex(SystemExit, "Invalid web"):
                web_dependencies_required(web)


class ArtifactReadinessTests(unittest.TestCase):
    def test_accepts_root_level_api_tests(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "apps/web").mkdir(parents=True)
            (root / "apps/web/package.json").write_text("{}")
            (root / "services/api").mkdir(parents=True)
            (root / "services/api/requirements.txt").write_text("pypdf>=5\n")
            (root / "tests").mkdir()
            (root / "tests/test_pdf_merge.py").write_text("def test_real_merge(): pass\n")
            self.assertEqual(vai001_artifacts(root), discover_api_tests(root))

    def test_rejects_autonomy_tests_only(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "apps/web").mkdir(parents=True)
            (root / "apps/web/package.json").write_text("{}")
            (root / "services/api").mkdir(parents=True)
            (root / "services/api/requirements.txt").write_text("pypdf>=5\n")
            (root / "tests").mkdir()
            (root / "tests/test_auto_dev.py").write_text("pass\n")
            with self.assertRaisesRegex(GateError, "No API/PDF"):
                vai001_artifacts(root)

    def test_reports_missing_manifest(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "apps/web").mkdir(parents=True)
            (root / "apps/web/package.json").write_text("{}")
            (root / "services/api/tests").mkdir(parents=True)
            (root / "services/api/tests/test_merge.py").write_text("def test_pdf(): pass\n")
            with self.assertRaisesRegex(GateError, "API manifest missing"):
                vai001_artifacts(root)


if __name__ == "__main__":
    unittest.main()
