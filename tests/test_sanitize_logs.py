"""Synthetic-only log scrubbing tests."""
from unittest import TestCase
from scripts.sanitize_logs import sanitize


class LogSanitizerTests(TestCase):
    def test_redacts_tokens_and_private_address(self):
        value = "ghp_" + "A" * 30
        sample = "Authorization: Bearer SYNTHETIC\n" + value + "\n10.20.30.40"
        result = sanitize(sample)
        self.assertNotIn(value, result)
        self.assertNotIn("SYNTHETIC", result)
        self.assertNotIn("10.20.30.40", result)
        self.assertIn("[REDACTED", result)

    def test_keeps_nonprivate_build_information(self):
        self.assertIn("pytest passed", sanitize("pytest passed"))
