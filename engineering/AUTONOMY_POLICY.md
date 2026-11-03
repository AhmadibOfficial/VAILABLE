# VAILABLE engineering autonomy policy

## Allowed after local activation
- Choose the first dependency-unblocked ROADMAP task.
- Develop changes in a **separate worktree** and feature branch only.
- Run local unit, security and integration checks.
- Save evidence under `.vailable/runs/` (ignored by git).
- Commit verified code on a feature branch, and optionally push/open a **draft** PR with explicit `--publish` mode.

## Approval gates
- Never merge, deploy, configure cloud resources, purchase services, change DNS, rotate credentials or handle customer documents automatically.
- Never modify branches `main` or `develop` directly.
- Never disable or modify branch protection, CI or the local autonomy runner as part of an agent task.
- Do not weaken tests to get green status; do not claim features implemented until demonstrated.
- Never send real documents, secrets or credentials to a model or remote service without explicit consent.
- Do not install dependencies or execute retrieved scripts with elevated privilege.
- Do not delete or modify other projects, Docker volumes, databases or user system files.
- Bounded retries: default is **one task per run**. A failed task remains available for inspection.
- GitHub Actions checks are an optional second layer, not proof of deploy readiness.

## Required reporting
Each draft PR should describe what changed, tests run, remaining risks, and any licensing or fidelity limits.

## Additional AI-assisted confidentiality gates
- Follow AGENTS.md and docs/security/AI_ASSISTED_DEV.md; use only synthetic data and narrow task-scoped context.
- Isolated Git worktrees, .gitignore and Codex workspace-write do not enforce read isolation. Refuse agent execution without a reviewed external OS/container wrapper.
- Strip ambient cloud/token environment variables and use dedicated HOME/CODEX_HOME.
- Scan staged files for secrets and unapproved dependencies before agent commits. Install Gitleaks pre-commit enforcement.
- Never waive CI or independent AppSec review, self-approve changes, or give agents production credentials or deployment pathways.
- Verify provider confidentiality agreements before making training/retention claims.
