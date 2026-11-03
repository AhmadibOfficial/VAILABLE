"""Synthetic confidentiality and agent boundary tests."""
import os
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

    def test_agent_does_not_inherit_ambient_cloud_keys(self):
        with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "SYNTHETIC",
                                     "GITHUB_TOKEN": "SYNTHETIC"}):
            env = restricted_agent_environment()
            self.assertNotIn("AWS_ACCESS_KEY_ID", env)
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertIn("CODEX_HOME", env)
