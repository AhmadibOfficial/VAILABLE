#!/usr/bin/env python3
"""Dependency-free base verification. Extend for installed app toolchains."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=cwd, check=False, timeout=300)
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    files = [str(p) for parent in (ROOT / "scripts", ROOT / "tests")
             for p in parent.rglob("*.py") if "__pycache__" not in p.parts]
    if files:
        run([sys.executable, "-m", "py_compile", *files])
    web = ROOT / "apps/web"
    if (web / "package.json").exists():
        if not (web / "node_modules").is_dir():
            raise SystemExit("Web app detected but dependencies missing: run npm ci in apps/web")
        run(["npm", "run", "lint", "--if-present"], web)
        run(["npm", "run", "typecheck", "--if-present"], web)
        run(["npm", "test", "--if-present"], web)
    api = ROOT / "services/api"
    if (api / "pyproject.toml").exists() or (api / "requirements.txt").exists():
        if not (api / "tests").is_dir() or not any((api / "tests").rglob("test_*.py")):
            raise SystemExit("API manifest exists but no real API tests in services/api/tests")
        # Fail closed if the project's test tooling is unavailable.
        run([sys.executable, "-m", "pytest", "-q", str(api / "tests")])
    print("All configured local verification gates passed.")


if __name__ == "__main__":
    main()
