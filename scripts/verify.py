#!/usr/bin/env python3
"""Fail-closed local verification for base repo or a validated task worktree."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=cwd, check=False, timeout=300)
    if result.returncode:
        raise SystemExit(result.returncode)


def discover_api_tests(root: Path) -> list[Path]:
    api_tests = root / "services/api/tests"
    tests = sorted(api_tests.rglob("test_*.py")) if api_tests.is_dir() else []
    ordinary_tests = root / "tests"
    if ordinary_tests.is_dir():
        tests += sorted(path for path in ordinary_tests.rglob("test_*.py")
                        if any(term in path.name.lower() for term in
                               ("merge", "pdf", "api", "worker", "vai001", "vai_001")))
    return sorted(set(tests))


def main(root: Path) -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], root)
    files = [str(p) for parent in (root / "scripts", root / "tests")
             for p in parent.rglob("*.py") if "__pycache__" not in p.parts]
    if files:
        run([sys.executable, "-m", "py_compile", *files], root)
    web = root / "apps/web"
    if (web / "package.json").exists():
        if not (web / "node_modules").is_dir():
            raise SystemExit("Web dependencies missing: run npm ci in apps/web after inspecting package manifests")
        run(["npm", "run", "lint", "--if-present"], web)
        run(["npm", "run", "typecheck", "--if-present"], web)
        run(["npm", "test", "--if-present"], web)
    api = root / "services/api"
    if any((api / name).exists() for name in
           ("pyproject.toml", "requirements.txt", "requirements-dev.txt")):
        tests = discover_api_tests(root)
        if not tests:
            raise SystemExit("API manifest present but no meaningful PDF/API tests found in services/api/tests or tests")
        run([sys.executable, "-m", "pytest", "-q", *[str(t) for t in tests]], root)
    print("All configured local verification gates passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VAILABLE local test gates")
    parser.add_argument("--root", type=Path, default=ROOT, help="Project root to verify")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "scripts/verify.py").is_file() or not (root / "engineering/ROADMAP.json").is_file():
        parser.error("--root must point at a VAILABLE project or approved worktree")
    main(root)
