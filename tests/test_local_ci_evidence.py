"""Unit tests for the offline evidence tool (no GitHub access)."""
from pathlib import Path
import os
import stat
import sys
import tempfile
import unittest

from scripts.local_ci_evidence import (
    interpreter_path, private_write, secure_output, validate_project,
    verification_environment,
)


class LocalEvidenceTests(unittest.TestCase):
    def test_preserves_virtualenv_interpreter_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            venv_bin = Path(tmp) / "venv" / "bin"
            venv_bin.mkdir(parents=True)
            alias = venv_bin / "python"
            alias.symlink_to(Path(sys.executable).resolve())
            selected = interpreter_path(alias)
            self.assertEqual(selected, alias.absolute())
            self.assertTrue(selected.is_file())
            self.assertNotEqual(selected, alias.resolve())

    def test_child_process_prefers_selected_virtualenv(self):
        with tempfile.TemporaryDirectory() as tmp:
            alias = Path(tmp) / "venv" / "bin" / "python"
            env = verification_environment(alias)
            self.assertEqual(env["PATH"].split(os.pathsep)[0], str(alias.parent))
            self.assertEqual(env["PATH"].split(os.pathsep, 1)[1],
                             os.environ.get("PATH", ""))

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
