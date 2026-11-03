#!/usr/bin/env python3
"""Offline secret/file exposure gate. Emits filenames and rule IDs, not secret values."""
from __future__ import annotations
import argparse
from pathlib import PurePosixPath
import re
import subprocess
import sys

MAX_SCAN_BYTES = 5 * 1024 * 1024
PATTERNS = {
    "private-key": re.compile(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "openai-token": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{24,}"),
    "aws-access-key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "slack-token": re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
    "secret-assignment": re.compile(rb"(?im)^\s*(?:PASSWORD|DB_PASSWORD|API_SECRET|PRIVATE_TOKEN|CLIENT_SECRET)\s*[:=]\s*['\"]?[A-Za-z0-9_+/-]{12,}"),
}
DENIED_EXT = {".pem", ".key", ".p12", ".pfx", ".sqlite", ".db", ".bak",
              ".dump", ".pdf", ".doc", ".docx", ".xlsx", ".csv", ".jks", ".keystore"}
DENIED_NAMES = {"id_rsa", "id_ed25519", ".npmrc", ".pypirc", "credentials",
                "credentials.json", "service-account.json", "config.json.bak"}
DENIED_DIRS = {"uploads", "customer-data", "client-data", "private-data", "backups"}


def risky_name(name: str) -> bool:
    path = PurePosixPath(name)
    parts = [part.lower() for part in path.parts]
    if not parts or ".." in parts:
        return True
    if any(p == ".env" or (p.startswith(".env.") and p != ".env.example")
           for p in parts):
        return True
    return (any(p in DENIED_DIRS for p in parts) or
            path.suffix.lower() in DENIED_EXT or
            path.name.lower() in DENIED_NAMES or
            path.name.lower().endswith((".secret", ".credentials", ".kubeconfig")))


def violations(name: str, payload: bytes) -> list[str]:
    findings = ["sensitive-file-path"] if risky_name(name) else []
    if len(payload) > MAX_SCAN_BYTES:
        return findings + ["scan-size-limit"]
    if b"\x00" in payload and not name.endswith((".png", ".jpg", ".jpeg", ".webp", ".ico")):
        findings.append("unexpected-binary")
    return findings + [rule for rule, pattern in PATTERNS.items() if pattern.search(payload)]


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)


def scan(mode: str) -> list[tuple[str, str]]:
    if mode == "staged":
        paths = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    elif mode == "tracked":
        paths = git("ls-files", "--cached", "-z")
    else:
        raise ValueError("Unsupported scan mode")
    results = []
    for raw in paths.split(b"\x00"):
        if not raw:
            continue
        name = raw.decode("utf-8", errors="replace")
        try:
            payload = git("show", ":" + name)
        except subprocess.CalledProcessError:
            results.append((name, "unreadable-git-index"))
            continue
        results += [(name, rule) for rule in violations(name, payload)]
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="VAILABLE offline confidentiality gate")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--staged", action="store_true")
    group.add_argument("--tracked", action="store_true")
    args = parser.parse_args()
    try:
        problems = scan("staged" if args.staged else "tracked")
    except subprocess.CalledProcessError:
        print("BLOCK: Git index cannot be read", file=sys.stderr)
        return 1
    if problems:
        for name, rule in problems:
            print(f"BLOCK: {name}: {rule} (matched values suppressed)", file=sys.stderr)
        return 1
    print("PASS: offline confidentiality gate (not a substitute for Gitleaks/manual review)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
