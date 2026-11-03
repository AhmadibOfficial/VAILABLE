#!/usr/bin/env python3
"""Fail closed on unapproved direct Python/npm dependencies."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.!+-]+)$")


def collect_requirements(root: Path) -> dict[str, str]:
    found = {}
    for path in (root / "services/api/requirements.txt",
                 root / "services/api/requirements-dev.txt"):
        if not path.is_file():
            raise ValueError("Missing dependency manifest: " + path.name)
        for n, raw in enumerate(path.read_text().splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line == "-r requirements.txt" and path.name == "requirements-dev.txt":
                continue
            match = PIN.fullmatch(line)
            if match is None:
                raise ValueError(f"Unpinned or unsupported dependency at {path.name}:{n}")
            name, version = match.groups()
            key = re.sub(r"[-_.]+", "-", name).lower()
            if key in found and found[key] != version:
                raise ValueError("Conflicting dependency pin: " + key)
            found[key] = version
    return found


def check(root: Path) -> None:
    approved = json.loads((root / "engineering/DEPENDENCY_APPROVALS.json").read_text())
    if collect_requirements(root) != approved["python"]:
        raise ValueError("Python dependency versions differ from approval register")
    pkg = json.loads((root / "apps/web/package.json").read_text())
    npm = {}
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        val = pkg.get(section, {})
        if not isinstance(val, dict):
            raise ValueError("Invalid npm dependency section")
        npm.update(val)
    if npm != approved["npm"]:
        raise ValueError("npm dependencies differ from approval register")
    lock = json.loads((root / "apps/web/package-lock.json").read_text())
    if not isinstance(lock.get("packages"), dict) or "" not in lock["packages"]:
        raise ValueError("Missing or malformed npm lockfile")
    if npm and len(lock["packages"]) <= 1:
        raise ValueError("npm lockfile is incomplete")


def main() -> int:
    try:
        check(ROOT)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"BLOCK: dependency approval gate: {exc}", file=sys.stderr)
        return 1
    print("PASS: approved direct dependency pins (not a vulnerability/provenance audit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
