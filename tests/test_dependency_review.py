"""Test pinned dependency validation with synthetic manifests."""
from pathlib import Path
import tempfile
from unittest import TestCase
from scripts.dependency_review import collect_requirements


class DependencyTests(TestCase):
    def test_rejects_ranges(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "services/api"
            p.mkdir(parents=True)
            (p / "requirements.txt").write_text("danger>=1\n")
            (p / "requirements-dev.txt").write_text("-r requirements.txt\n")
            with self.assertRaisesRegex(ValueError, "Unpinned"):
                collect_requirements(Path(d))

    def test_normalizes_pins(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "services/api"
            p.mkdir(parents=True)
            (p / "requirements.txt").write_text("My_Package==1.2.3\n")
            (p / "requirements-dev.txt").write_text("-r requirements.txt\nmy-package==1.2.3\n")
            self.assertEqual(collect_requirements(Path(d)), {"my-package": "1.2.3"})
