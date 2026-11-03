#!/usr/bin/env python3
"""Best-effort log sanitizer; human review is mandatory before sharing."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_LOG_ROOT = ROOT / ".vailable/runs"
PRIVATE_PATTERNS = (
    (re.compile(r"(?is)-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED:PRIVATE-KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "[REDACTED:GITHUB-TOKEN]"),
    (re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b"), "[REDACTED:API-TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED:AWS-KEY]"),
    (re.compile(r"(?i)(authorization:\s*bearer\s+)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED:EMAIL]"),
    (re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"), "[REDACTED:PRIVATE-IP]"),
)


def sanitize(text: str) -> str:
    for pattern, replacement in PRIVATE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize an AI run log")
    parser.add_argument("log", type=Path)
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()
    if args.log.is_symlink():
        parser.error("Refusing symlinked logs")
    path = args.log.resolve()
    if not path.is_file():
        parser.error("Must be an existing regular log file")
    content = sanitize(path.read_text(encoding="utf-8", errors="replace"))
    if args.in_place:
        if not path.is_relative_to(PRIVATE_LOG_ROOT.resolve()):
            parser.error("In-place edits restricted to ignored .vailable/runs directory")
        path.write_text(content, encoding="utf-8")
        path.chmod(0o600)
        print("Log sanitized in private runtime directory; review manually before sharing.")
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
