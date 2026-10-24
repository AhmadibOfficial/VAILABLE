"""Unit tests for the offline evidence tool (no GitHub access)."""
from pathlib import Path
import stat
import tempfile
import unittest

from scripts.local_ci_evidence import private_write, secure_output, validate_project


class LocalEvidenceTests(unittest.TestCase):
    def test_refuses_unimplemented_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "missing engineering/ROADMAP.json"):
                validate_project(Path(tmp))

    def test_secure_evidence_permissions_and_exclusive_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "evidence"
            secure_output(folder)
            self.assertEqual(stat.S_IMODE(folder.stat().st_mode), 0o700)
            path = folder / "report.json"
            private_write(path, b"{}")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                private_write(path, b"do not overwrite")
            self.assertEqual(path.read_bytes(), b"{}")


if __name__ == "__main__":
    unittest.main()
