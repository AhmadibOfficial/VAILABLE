# AI-assisted engineering — VAILABLE security controls

**Status: proposed protections on the VAI-001 draft branch; not production approval.**

## Secrets and confidential data
- Use synthetic PDFs and schemas only. Do not send personal information, client documents, source secrets, production infrastructure addresses, sensitive stack traces or raw logs to models.
- Manually sanitize prompts and logs; pattern scanners do not guarantee detection of all secrets.
- .gitignore prevents tracking ignored files, **not filesystem reads**. Do not confuse agent instructions with access control.
- Verify the chosen AI provider's actual contract, retention/training settings, data processing terms and opt-out policy before sharing confidential material. No unconditional zero-training/zero-retention claim is made.

## Isolated AI runtime
- VAILABLE_AGENT_WRAPPER must point to an independently reviewed, executable launcher **outside the repository**. The runner refuses AI execution without it; this is fail-closed configuration, not proof that the launcher implements isolation.
- The wrapper is responsible for real OS/container/VM read/write isolation: mount only the sanitized worktree; do not mount host HOME, SSH agent, cloud credentials, sibling repos, production sockets or private documents. Minimize network egress to required AI service endpoints only.
- The runner supplies a dedicated private HOME/CODEX_HOME and an allowlist of non-secret environment variables. Set up separate least-privilege AI credentials in the sandbox, not production credentials.
- Codex workspace-write and isolated Git worktrees alone are **insufficient** for host read isolation.

## Git, dependencies and review
1. Vet and install the official Gitleaks v8 executable, then run: sh scripts/install_security_hooks.sh
2. Verify tracked/staged content: python3 scripts/security_gate.py --tracked (or --staged).
3. Verify direct pinned dependencies: python3 scripts/dependency_review.py.
4. Inspect each new package's spelling, registry publisher, repository, licenses, advisories, signatures/provenance when available and transitive graph. Update engineering/DEPENDENCY_APPROVALS.json only after human review.
5. Run full unit/API/browser tests, Bandit SAST, dependency advisory scanning, and independent human AppSec review before merge.
6. Configure GitHub rulesets to require independent review and passing CI; CODEOWNERS and PR checklists alone do not enforce this. AI-authored changes are never self-approved.
7. Production deploy access, secrets, webhooks and environment-specific privileges must be held outside coding agents and require explicit approval.

## Known limitations
- Hook installation is opt-in and requires a vetted local Gitleaks; GitHub API commits bypass local hooks, hence CI scans are still required.
- GitHub Actions remains billing-restricted; no cloud CI success is claimed.
- The repository was observed as **public**. Confirm intended visibility; later changing it to private does not undo earlier exposure.
- The PDF worker still requires independently verified filesystem/network isolation before accepting untrusted public uploads.
- No merge, deployment or dependent VAI-002 milestone is approved by this document.
