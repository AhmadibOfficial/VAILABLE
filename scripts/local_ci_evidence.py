#!/usr/bin/env python3
"""Run VAILABLE verification locally and record bounded, private evidence.

This is NOT a GitHub Actions result, cryptographic attestation or independent review.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


def git(project: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(project), *args], text=True, stderr=subprocess.DEVNULL
    ).strip()


def validate_project(project: Path) -> None:
    for name in ("engineering/ROADMAP.json", "services/api/app.py", "apps/web/package.json"):
        if not (project / name).is_file():
            raise ValueError(f"Not an implemented VAILABLE worktree: missing {name}")


def secure_output(directory: Path) -> None:
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if stat.S_IMODE(directory.stat().st_mode) & 0o077:
        raise ValueError("Evidence directory must not be accessible by group or others")


def private_write(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="VAILABLE local-only verification evidence")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--verifier", type=Path, required=True,
                        help="Path to the current main-branch scripts/verify.py supporting --root")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--output", type=Path, default=Path(".vailable/evidence"))
    parser.add_argument("--expected-branch", default="agent/vai-001")
    args = parser.parse_args()

    project, verifier, python = (value.resolve() for value in
                                 (args.project, args.verifier, args.python))
    try:
        validate_project(project)
        if not verifier.is_file() or not python.is_file():
            raise ValueError("Verifier or Python interpreter missing")
        if Path(git(project, "rev-parse", "--show-toplevel")).resolve() != project:
            raise ValueError("Project is not its own Git worktree")
        branch = git(project, "branch", "--show-current")
        if branch != args.expected_branch:
            raise ValueError(f"Unexpected branch: {branch}")
        if git(project, "status", "--porcelain"):
            raise ValueError("Worktree has uncommitted or untracked changes")
        commit = git(project, "rev-parse", "HEAD")
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))

    output = args.output.resolve()
    try:
        secure_output(output)
    except ValueError as error:
        parser.error(str(error))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"VAI001-{commit[:12]}-{timestamp}"
    command = [str(python), str(verifier), "--root", str(project)]
    print(f"Running local tests for {commit[:12]} on {branch}...", flush=True)
    try:
        run = subprocess.run(command, cwd=project, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=1200, check=False)
        log_data = run.stdout
        result_code = run.returncode
    except subprocess.TimeoutExpired as error:
        log_data = (error.stdout or b"") + b"\nTIMEOUT: verification exceeded 1200 seconds\n"
        result_code = 124

    clean_after = not bool(git(project, "status", "--porcelain"))
    report = {
        "schema": 1, "subject_commit": commit, "branch": branch,
        "utc_timestamp": timestamp, "result": "passed" if result_code == 0 and clean_after else "failed",
        "verifier_exit_code": result_code, "worktree_clean_after": clean_after,
        "log_sha256": hashlib.sha256(log_data).hexdigest(),
        "provenance": "Local Kali execution only; not GitHub CI or independent review",
    }
    try:
        private_write(output / (stem + ".log"), log_data)
        private_write(output / (stem + ".json"),
                      (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    except FileExistsError:
        parser.error("Evidence filename collision; retry with a new UTC timestamp")

    print(f"{report['result'].upper()}: local evidence in {output / (stem + '.json')}")
    return 0 if report["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
