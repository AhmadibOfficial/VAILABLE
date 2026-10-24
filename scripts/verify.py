#!/usr/bin/env python3
"""Fail-closed local verification for base repo or a validated task worktree."""
from __future__ import annotations
import argparse
import json
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


def web_dependencies_required(web: Path) -> bool:
    """Validate a real npm test script and determine whether node_modules is required.

    A dependency-free static frontend may run npm ci successfully without
    creating node_modules. We must not mistake that for an install failure.
    """
    try:
        manifest = json.loads((web / "package.json").read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Invalid web package.json: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("scripts"), dict):
        raise SystemExit("Web manifest must include actual npm scripts")
    test_script = manifest["scripts"].get("test", "")
    if not isinstance(test_script, str) or not test_script.strip():
        raise SystemExit("Web manifest lacks a real npm test command")
    if test_script.strip() in {"true", ":", "echo OK", "echo success"}:
        raise SystemExit("Web test script is a no-op and cannot verify real code")
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        deps = manifest.get(section, {})
        if not isinstance(deps, dict):
            raise SystemExit(f"Web manifest {section} must be an object")
        if deps:
            return True
    return False


def main(root: Path) -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], root)
    files = [str(p) for parent in (root / "scripts", root / "tests")
             for p in parent.rglob("*.py") if "__pycache__" not in p.parts]
    if files:
        run([sys.executable, "-m", "py_compile", *files], root)
    web = root / "apps/web"
    if (web / "package.json").exists():
        dependencies_required = web_dependencies_required(web)
        if dependencies_required and not (web / "node_modules").is_dir():
            raise SystemExit("Web dependencies missing: review package-lock.json and run npm ci in apps/web")
        run(["npm", "run", "lint", "--if-present"], web)
        run(["npm", "run", "typecheck", "--if-present"], web)
        run(["npm", "test"], web)
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
