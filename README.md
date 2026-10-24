# VAILABLE — Autonomous Development Starter

**Status:** Starter automation is implemented and tested. Product functionality is still in the VAI-001 task queue; this package is **not** a working online PDF service.

**Principle:** one bounded AI development task per run, in an isolated git worktree, local tests, optional draft PR; **never auto-merge or deploy**.

## What is included

- `docs/product/BLUEPRINT.md`: the VAILABLE product specification and complete feature registry.
- `engineering/ROADMAP.json`: twelve dependency-gated coding tasks, VAI-001 to VAI-012.
- `engineering/PROGRESS.json`: checked-in record of reviewed/merged tasks. A completed task is recorded **only on its feature branch** until merged.
- `engineering/AUTONOMY_POLICY.md`: non-negotiable change and approval boundaries.
- `scripts/auto_dev.py`: actual Codex CLI orchestration (selection, task worktree, testing, safety scan, commit, optional draft PR).
- `scripts/verify.py`: local test runner and conditional web/API gates.
- `tests/`: stdlib unit tests of automation and permissions.
- `.github/workflows/ci.yml`: optional GitHub CI; may not run if GitHub account billing/actions are blocked.
- `scripts/install_user_timer.sh`: **optional**, explicitly invoked daily scheduling. Nothing is scheduled or run persistently by merely extracting this archive.

## 1. Install in a NEW directory

On Kali Linux, inspect this ZIP before extracting. **Do not overwrite another project.**

```bash
test ! -e "$HOME/VAILABLE" || { echo "STOP: ~/VAILABLE already exists"; exit 2; }
mkdir "$HOME/VAILABLE"
unzip "$HOME/Downloads/VAILABLE_Autonomous_Development_Starter.zip" -d "$HOME/VAILABLE"
cd "$HOME/VAILABLE"
python3 scripts/auto_dev.py status
python3 scripts/auto_dev.py verify
```

If you extract in another directory, the runner automatically finds its parent repository root.

## 2. Initialize your first local commit

```bash
git init -b main
git add .
git commit -m "chore: initialize VAILABLE autonomous engineering"
```

If Git requests author info, configure your preferred Git identity explicitly.

## 3. Install and sign in to Codex

Install the official Codex CLI according to its current documentation at https://developers.openai.com/codex/cli/ and authenticate. The runner **does not** install dependencies, subscribe to paid services or request keys. Codex may require a supported subscription or API access; costs and availability depend on your account. The runner assumes commands `codex`, `python3` and `git` are on PATH.

```bash
codex --version
codex login
```

## 4. Preview and launch VAI-001

```bash
python3 scripts/auto_dev.py plan
python3 scripts/auto_dev.py once
```

The second command:
1. Checks that `main` is clean.
2. Creates `agent/vai-001` in `.vailable/worktrees/vai-001/` **without modifying your main branch**.
3. Invokes Codex with a bounded task prompt.
4. Runs verification and rejects protected/secret-like files.
5. Commits a passing proposal on the worktree branch; if a check fails, preserves the worktree and log for investigation.

If the task cannot complete because dependencies are unavailable, it **stops rather than claiming success**. Review the log at `.vailable/runs/` (contains agent output; avoid sharing it without inspecting).

## 5. Enable draft GitHub PRs when the repository is ready

The GitHub repo `AhmadibOfficial/VAILABLE` was not found during preparation. Create a **private** new empty repository under the intended account when ready. Example with GitHub CLI after reviewing the command:

```bash
gh auth login
gh repo create AhmadibOfficial/VAILABLE --private --source=. --remote=origin --push
```

To automatically propose a **new** task on a draft PR, run:

```bash
python3 scripts/auto_dev.py once --publish
```

**Important:** `--publish` is only for a new task that has not yet generated a branch. If a local task branch already exists, review and publish that branch manually using `git -C .vailable/worktrees/vai-001 push -u origin agent/vai-001`, then `gh pr create --draft --base main --head agent/vai-001`. The runner will refuse to recreate or overwrite it.

Only after review and merge of the PR will `engineering/PROGRESS.json` on `main` list the task as completed. After updating `main` via `git pull --ff-only`, a subsequent run will select the next task automatically.

## 6. Optional daily automation on Kali

After confirming the repository, Codex CLI and GitHub CLI all work, you can set up a 09:30 **local-time** user-systemd timer with:

```bash
bash scripts/install_user_timer.sh
systemctl --user list-timers --all | grep vailable
```

Scheduling is opt-in. It runs **one** task per day and opens a draft PR if code and checks pass. It cannot operate if your device is off (depending on user systemd availability), authentication expires, a prerequisite fails, or an earlier PR has not merged. It does not silently merge PRs.

To disable:

```bash
systemctl --user disable --now vailable-dev.timer
```

This timer assumes the default local Python is `/usr/bin/python3`; modify the unit if your machine uses a different interpreter. Run `systemctl --user daemon-reload` after manual changes.

## Limits and safety

- **No unattended ChatGPT turn** can access or run a job on your Kali computer. The local runner must be activated by you and your computer or CI infrastructure must be running.
- **No claim of full autonomy:** agent decisions, dependencies, tests, publishing and branch protections can require human intervention.
- **No GitHub repo was created**, and no production service was deployed as part of this package.
- The verifier checks configured tests; an implementation needs additional fidelity, safety and end-to-end tests before production.
- A local worktree is not a hard security sandbox. For stronger isolation, run the coding agent inside a properly configured container or VM with limited credentials and no sensitive mounted directories.
- Do not place real customer PDFs, production API keys, or private company data inside an agent worktree.
- `gh` and Codex may require access to external services; credentials must be provisioned and maintained through their own secure authentication workflows.
- Protect `main` with review requirements when supported. If GitHub Actions reports account billing issues, local verification still works, but do not interpret unavailable CI as a green check.
