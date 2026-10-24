#!/usr/bin/env python3
"""VAILABLE bounded local Codex orchestrator.

Runs one queued task in a disposable git worktree, validates, commits and
optionally offers a draft PR. Never merges or deploys.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "engineering/ROADMAP.json"
PROGRESS = ROOT / "engineering/PROGRESS.json"
STATE_DIR = ROOT / ".vailable"
ALLOWED_ROOTS = {"apps", "services", "packages", "docs", "tests", "engineering", "scripts", "infrastructure"}
ALLOWED_TOP_FILES = {"README.md", "package.json", "pyproject.toml", "tsconfig.json", "pnpm-workspace.yaml", "package-lock.json"}
PROTECTED = {
    "engineering/ROADMAP.json", "engineering/PROGRESS.json",
    "engineering/AUTONOMY_POLICY.md", "scripts/auto_dev.py",
    "scripts/verify.py", "docs/security/THREAT_MODEL.md",
}
BAD_PARTS = {".git", ".vailable", "node_modules", "__pycache__", ".next"}
SECRET_RE = re.compile(
    r"(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"sk-(?:proj-)?[A-Za-z0-9_-]{24,}|"
    r"AKIA[0-9A-Z]{16})"
)


class GateError(RuntimeError):
    pass


def invoke(*cmd: str, cwd: Path = ROOT, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False, timeout=40)
    if check and result.returncode:
        raise GateError(f"Command failed: {' '.join(cmd)}\n{result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def next_task(roadmap: dict, progress: dict) -> dict | None:
    tasks = roadmap["tasks"]
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        raise GateError("Duplicate roadmap task IDs")
    done = set(progress["completed_tasks"])
    if not done.issubset(ids):
        raise GateError("Progress contains unknown task IDs")
    for t in tasks:
        if not set(t["depends_on"]).issubset(ids):
            raise GateError("Roadmap refers to an unknown dependency")
        if t["id"] not in done and set(t["depends_on"]).issubset(done):
            return t
    if len(done) == len(tasks):
        return None
    raise GateError("No task ready; check roadmap dependency cycle")


def safe_path(name: str) -> bool:
    if not name or "\\" in name or name.startswith("/"):
        return False
    p = PurePosixPath(name)
    if ".." in p.parts or any(part in BAD_PARTS for part in p.parts):
        return False
    if any(part == ".env" or part.startswith(".env.") for part in p.parts):
        return False
    if any(part.lower().endswith((".pem", ".key", ".p12", ".pfx", ".sqlite", ".db")) for part in p.parts):
        return False
    if re.search(r"(^|[._/-])(secret|credential|token|id_rsa)(s)?([._/-]|$)", name, re.I):
        return False
    if name in PROTECTED or name.startswith(".github/"):
        return False
    if len(p.parts) == 1:
        return name in ALLOWED_TOP_FILES
    return p.parts[0] in ALLOWED_ROOTS


def working_changes(worktree: Path, allow_progress: bool = False) -> list[str]:
    deleted = invoke("git", "diff", "--name-only", "--diff-filter=D", "HEAD", cwd=worktree)
    if deleted:
        raise GateError(f"Agent deleted tracked files; manual review required: {deleted}")
    renamed = invoke("git", "diff", "--name-only", "--diff-filter=R", "HEAD", cwd=worktree)
    if renamed:
        raise GateError(f"Agent renamed tracked files; manual review required: {renamed}")
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "-z", "HEAD"], cwd=worktree,
        check=True, capture_output=True,
    ).stdout.split(b"\0")
    new = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=worktree,
        check=True, capture_output=True,
    ).stdout.split(b"\0")
    names = sorted({n.decode("utf-8") for n in tracked + new if n})
    for name in names:
        p = worktree / name
        if not (safe_path(name) or (allow_progress and name == "engineering/PROGRESS.json")) or p.is_symlink() or not p.is_file():
            raise GateError(f"Disallowed change: {name}")
        if p.stat().st_size > 4 * 1024 * 1024:
            raise GateError(f"File exceeds 4 MiB review threshold: {name}")
        if p.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".json", ".md", ".yaml", ".yml", ".sh", ".txt"}:
            try:
                content = p.read_text(encoding="utf-8")
            except UnicodeError as e:
                raise GateError(f"Non-text file in code path: {name}") from e
            if SECRET_RE.search(content):
                raise GateError(f"Possible embedded credential: {name}")
    return names


def task_prompt(task: dict) -> str:
    return f"""You are developing VAILABLE (an original PDF and document platform).
Complete exactly task {task['id']}: {task['title']}.
Objectives: {json.dumps(task['objectives'], ensure_ascii=False)}
Acceptance: {json.dumps(task['acceptance'], ensure_ascii=False)}
Read docs/product/BLUEPRINT.md, engineering/AUTONOMY_POLICY.md and docs/security/THREAT_MODEL.md first.
You are inside a task-specific git worktree. Modify this worktree only.
Implement real, production-minded code and deterministic tests using synthetic fixtures.
Keep every unimplemented feature visibly marked Coming Soon. Do not fake success.
Never access user documents, credential stores, cloud resources or other repositories.
Never change .github workflows, automation runner, policy, ROADMAP or PROGRESS.
Do not merge, deploy, create accounts, publish, change DNS or purchase resources.
Do not remove files. Respect open-source licenses and note conversion limitations.
When finished, run python3 scripts/verify.py and explain results.
If dependencies are missing, document precise setup rather than bypassing verification.
"""


def safe_git_base(base: str) -> None:
    if base not in ("main", "develop"):
        raise GateError("Only main or develop may be the checked-out base branch")
    if not (ROOT / ".git").exists():
        raise GateError("Initialize and commit a Git repository in this new project first")
    if invoke("git", "rev-parse", "--show-toplevel") != str(ROOT):
        raise GateError("Wrong Git repository root")
    if invoke("git", "symbolic-ref", "--short", "HEAD") != base:
        raise GateError(f"Checkout the approved base branch {base} first")
    if invoke("git", "status", "--porcelain"):
        raise GateError("Base repository has uncommitted changes; refusing to run")
    invoke("git", "rev-parse", "--verify", "HEAD")


def check_publish_preflight() -> None:
    if not shutil.which("gh"):
        raise GateError("GitHub CLI (gh) missing; rerun without --publish")
    remote = invoke("git", "remote", "get-url", "origin")
    if not re.fullmatch(r"(?:https://github\.com/|git@github\.com:)(?:AhmadibOfficial/)[Vv][Aa][Ii][Ll][Aa][Bb][Ll][Ee](?:\.git)?", remote):
        raise GateError("Refusing to publish to origin other than AhmadibOfficial/VAILABLE")
    invoke("gh", "auth", "status")


def perform(task: dict, base: str, publish: bool, timeout: int) -> None:
    if not shutil.which("codex"):
        raise GateError("Codex CLI is missing. Install and sign in, then rerun")
    if publish:
        check_publish_preflight()
    branch = "agent/" + task["id"].lower()
    if subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
                      cwd=ROOT, check=False, capture_output=True).returncode == 0:
        raise GateError(f"Branch {branch} already exists. Review or merge it before continuing")
    runpath = STATE_DIR / "runs"
    runpath.mkdir(parents=True, exist_ok=True)
    worktree = STATE_DIR / "worktrees" / task["id"].lower()
    if worktree.exists():
        raise GateError(f"Worktree already exists, refusing to overwrite: {worktree}")
    invoke("git", "worktree", "add", "-b", branch, str(worktree), base)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log = runpath / f"{task['id']}-{stamp}.log"
    print(f"Running {task['id']} in isolated worktree: {worktree}", flush=True)
    try:
        with log.open("w", encoding="utf-8") as out:
            result = subprocess.run(
                ["codex", "exec", "--sandbox", "workspace-write", "--ask-for-approval", "never", "-"],
                input=task_prompt(task), stdout=out, stderr=subprocess.STDOUT,
                text=True, cwd=worktree, check=False, timeout=timeout,
            )
        if result.returncode:
            raise GateError(f"Codex exited {result.returncode}; see {log}")
        changes = working_changes(worktree)
        if not changes:
            raise GateError(f"Agent did not change any allowed files; see {log}")
        if task["id"] == "VAI-001":
            web_manifest = worktree / "apps/web/package.json"
            api = worktree / "services/api"
            api_manifest = (api / "pyproject.toml").exists() or (api / "requirements.txt").exists()
            api_tests = api / "tests"
            if not web_manifest.is_file() or not api_manifest or not api_tests.is_dir() or not any(api_tests.rglob("test_*.py")):
                raise GateError("VAI-001 requires a real web app, API dependency manifest and API test files")
        with log.open("a", encoding="utf-8") as out:
            result = subprocess.run([sys.executable, "scripts/verify.py"],
                                    cwd=worktree, text=True, stdout=out,
                                    stderr=subprocess.STDOUT, timeout=900)
        if result.returncode:
            raise GateError(f"Verification failed; worktree preserved at {worktree}, log: {log}")
        progress_path = worktree / "engineering/PROGRESS.json"
        progress = read_json(progress_path)
        progress["completed_tasks"].append(task["id"])
        progress_path.write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
        changes = working_changes(worktree, allow_progress=True)
        invoke("git", "add", "--", *changes, cwd=worktree)
        invoke("git", "diff", "--cached", "--check", cwd=worktree)
        diff = invoke("git", "diff", "--cached", "--unified=0", cwd=worktree)
        for line in diff.splitlines():
            if line.startswith("+") and not line.startswith("+++") and SECRET_RE.search(line):
                raise GateError("Possible credential in staged diff; changes not committed")
        invoke("git", "commit", "-m", f"feat(vailable): {task['id']} {task['title']}", cwd=worktree)
        print(f"PASS: verified and committed {branch}; log: {log}", flush=True)
        if publish:
            invoke("git", "push", "-u", "origin", branch, cwd=worktree)
            body = (f"Automated development proposal for **{task['id']}**.\n\n"
                    f"**Acceptance targets:**\n" + "\n".join(f"- {a}" for a in task["acceptance"]) +
                    "\n\nLocal verification: `python3 scripts/verify.py` passed.\n"
                    "Review code, security, dependencies and output fidelity before merging.\n"
                    "No production deployment or merge was attempted.\n")
            url = invoke("gh", "pr", "create", "--draft", "--base", base, "--head", branch,
                         "--title", f"{task['id']}: {task['title']}", "--body", body, cwd=worktree)
            print(f"Draft PR opened: {url}")
        else:
            print("Local only: no push or PR. Use --publish on a future clean run after setup.")
        print("NEXT: Review and merge this proposal before starting a dependent task.")
    except subprocess.TimeoutExpired as e:
        raise GateError(f"Task or verification timed out; worktree retained for inspection. Log: {log}") from e


def main() -> int:
    parser = argparse.ArgumentParser(description="VAILABLE autonomous development runner")
    parser.add_argument("command", choices=["status", "plan", "verify", "once"])
    parser.add_argument("--base", default="main", choices=["main", "develop"])
    parser.add_argument("--publish", action="store_true", help="Push and open a draft GitHub PR")
    parser.add_argument("--timeout", type=int, default=2400)
    args = parser.parse_args()
    try:
        if args.command == "verify":
            subprocess.run([sys.executable, "scripts/verify.py"], cwd=ROOT, check=True)
            return 0
        roadmap = read_json(ROADMAP)
        progress = read_json(PROGRESS)
        task = next_task(roadmap, progress)
        if args.command == "status":
            print(f"Completed and merged: {len(progress['completed_tasks'])}/{len(roadmap['tasks'])}")
        if not task:
            print("No queued tasks remain")
            return 0
        print(f"Next: {task['id']} — {task['title']}")
        if args.command in {"status", "plan"}:
            for objective in task["objectives"]:
                print("  -", objective)
            return 0
        if args.timeout < 120 or args.timeout > 7200:
            raise GateError("--timeout must be 120 to 7200 seconds")
        safe_git_base(args.base)
        perform(task, args.base, args.publish, args.timeout)
        return 0
    except (GateError, subprocess.CalledProcessError) as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
