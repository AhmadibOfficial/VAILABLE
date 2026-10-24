# VAILABLE VAI-001 — Consolidated hardening and review batch

**Status:** Code changes proposed on the draft VAI-001 branch. This document is not an independent security review or production approval.

## Scope and implemented safeguards

- Only two browser asset filenames are exposed by `/assets/{name}`: `app.js` and `style.css`. The server no longer serves the entire application source directory.
- Interactive API documentation routes are disabled for this pre-release build.
- Upload parsing checks advertised body size before buffering; the streamed body still enforces the 20 MiB limit, regardless of the header.
- Security response headers include CSP, no-sniff, frame denial, no-referrer, CORP, restricted browser permissions and no-store responses.
- Synthetic tests verify source-file denial, header policy, advertised-size rejection, and browser asset behavior.
- Blue VAILABLE brand colors are applied without introducing external fonts, scripts, libraries or copied brand assets.

## Existing VAI-001 guardrails (not independently audited)

- 2–10 PDFs; per-file and aggregate request limits; 300-page and 25 MiB output bounds.
- Strict PDF parsing, rejection of encrypted/action/attachment PDFs and predictable failure messages.
- Isolated per-request temporary directories with cleanup, subprocess CPU/memory/file/process limits, no persistent document storage.
- Two in-flight processing slots with generic capacity failures.

## Release blockers and residual risks

1. The PDF parser subprocess is not isolated in its own filesystem and network namespaces. The current resource limits **do not establish network isolation**; enforce network egress and OS-level sandboxing before accepting untrusted public uploads.
2. No user account, authenticated storage, enterprise access control, signing or redaction is implemented.
3. Dependency pinning is not a vulnerability scan or complete transitive SBOM. Perform license/security review before production.
4. GitHub-hosted Actions is blocked by the account's confirmed billing/spending restriction. Local passing tests are not a substitute for a successful cloud CI run.
5. A reviewer independent of the coding agent must review request parsing, worker boundaries, PDF parser security, browser upload behavior and deployment configuration.
6. No deployed endpoint or production readiness is claimed by these changes.

## Local verification after synchronizing the branch

From `~/VAILABLE`, with the isolated environment previously installed:

```bash
ROOT="$PWD"
W="$ROOT/.vailable/worktrees/vai-001"
VENV="$ROOT/.vailable/venvs/vai-001"
PATH="$VENV/bin:$PATH" "$VENV/bin/python" scripts/verify.py --root "$W"
```

To collect a local-only evidence report, run `scripts/local_ci_evidence.py` from the feature worktree with the main-branch verifier and its isolated Python interpreter. Evidence is stored only under ignored, permission-restricted `.vailable/`, never committed or uploaded automatically.

**Merge gate:** Independent review and CI resolution are still required; do not merge, enable deployment, or mark VAI-002 active based on this document.
