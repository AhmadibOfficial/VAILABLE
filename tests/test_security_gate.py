"""Synthetic confidentiality and agent boundary tests."""
import os
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch
from scripts.security_gate import risky_name, violations, MAX_SCAN_BYTES
from scripts.auto_dev import isolated_agent_wrapper, restricted_agent_environment, GateError


class ConfidentialityTests(TestCase):
    def test_sensitive_paths(self):
        for name in (".env", "services/api/.env.production", ".npmrc",
                     "uploads/customer.pdf", "client-data/records.txt",
                     "backups/state.db", "customer.csv", "cert.pem"):
            with self.subTest(name=name):
                self.assertTrue(risky_name(name))
        self.assertFalse(risky_name(".env.example"))
        self.assertFalse(risky_name("apps/web/app.js"))

    def test_detects_synthetic_token(self):
        self.assertEqual(violations("settings.py", b"ghp_" + b"A" * 30),
                         ["github-token"])
        self.assertIn("scan-size-limit",
                      violations("large.py", b"X" * (MAX_SCAN_BYTES + 1)))

    def test_unconfigured_agent_is_blocked(self):
        with patch.dict(os.environ, {"VAILABLE_AGENT_WRAPPER": ""}):
            with self.assertRaises(GateError):
                isolated_agent_wrapper()

    def test_rejects_untrusted_isolation_wrapper(self):
        with tempfile.TemporaryDirectory() as directory:
            launcher = Path(directory) / "launcher"
            launcher.write_text("#!/bin/sh\nexit 0\n")
            launcher.chmod(0o777)
            with patch.dict(os.environ, {"VAILABLE_AGENT_WRAPPER": str(launcher)}):
                with self.assertRaisesRegex(GateError, "group/world-writable"):
                    isolated_agent_wrapper()
            launcher.chmod(0o700)
            link = Path(directory) / "link"
            link.symlink_to(launcher)
            with patch.dict(os.environ, {"VAILABLE_AGENT_WRAPPER": str(link)}):
                with self.assertRaisesRegex(GateError, "non-symlink"):
                    isolated_agent_wrapper()

    def test_agent_does_not_inherit_ambient_cloud_keys(self):
        with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "SYNTHETIC",
                                     "GITHUB_TOKEN": "SYNTHETIC"}):
            env = restricted_agent_environment()
            self.assertNotIn("AWS_ACCESS_KEY_ID", env)
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertIn("CODEX_HOME", env)
