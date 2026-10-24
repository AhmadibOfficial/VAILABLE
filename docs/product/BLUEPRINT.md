# VAILABLE — Product Blueprint (v0.1)

**Status:** Concept approved for planning; no implementation or deployment is claimed.  
**Product:** An original all-in-one PDF and document productivity platform.  
**Working tagline:** Your documents. Every tool. One place.  
**Reference for functional scope:** https://www.ilovepdf.com/ (feature reference, not a template to copy).  
**Platforms:** Responsive web first; Android/iOS and Windows/macOS/Linux later.  
**Date:** 2026-10-24.

## 1. Vision

VAILABLE helps individuals, teams and businesses organize, convert, edit, optimize, secure, sign and understand PDF documents via a fast, privacy-conscious and accessible interface. All interface components, brand elements and code must be independently designed and licensed appropriately.

## 2. Principles

1. A useful free core; communicate any processing, file-size or compute limits accurately rather than promising universal unlimited free service.
2. Guest access for basic tools; accounts for history, workflows, teams and paid capabilities.
3. Privacy by design: least privilege, minimal retention, consent for optional saved files and AI processing.
4. High processing fidelity with honest disclosure of conversion limitations.
5. Offline/local execution for feasible operations; server processing for compute-intensive or unsupported browser functions.
6. Source/license compliance reviewed before shipping.
7. Accessible, responsive, multilingual-ready user experience.

## 3. Feature registry

### 3.1 Organize PDF
| ID | Tool | Expected output | Priority |
| --- | --- | --- | --- |
| ORG-01 | Merge PDF | Ordered combined PDF | MVP |
| ORG-02 | Split PDF | Individual PDFs or zip of selected ranges | MVP |
| ORG-03 | Organize Pages | Reordered/deleted/inserted pages | MVP |
| ORG-04 | Rotate PDF | Rotated PDF pages | MVP |
| ORG-05 | Crop PDF | PDF with adjusted page crop regions | Phase 2 |
| ORG-06 | Page Numbers | Numbered PDF with placement controls | Phase 2 |
| ORG-07 | Repair PDF | Best-effort recovery; report unrecoverable material | Phase 2 |

### 3.2 Conversion
| ID | Tool | Expected output | Priority |
| --- | --- | --- | --- |
| CNV-01 | PDF to Word | Editable DOCX; state fidelity limitations | Phase 2 |
| CNV-02 | PDF to PowerPoint | Editable PPTX as feasible | Phase 3 |
| CNV-03 | PDF to Excel | Structured XLSX or CSV; preview tables | Phase 3 |
| CNV-04 | Word to PDF | Faithful PDF export | Phase 2 |
| CNV-05 | PowerPoint to PDF | PDF export | Phase 2 |
| CNV-06 | Excel to PDF | Configurable sheets/page scaling | Phase 2 |
| CNV-07 | PDF to JPG | Each page to image or embedded image extraction | MVP |
| CNV-08 | JPG/Images to PDF | Configurable order, size, fit and margins | MVP |
| CNV-09 | HTML to PDF | Sandboxed HTML or allowlisted URL capture | Phase 3 |
| CNV-10 | PDF to PDF/A | Validated archive PDF output | Phase 3 |
| CNV-11 | PDF to Markdown | Structured extraction including headings/tables where feasible | Phase 3 |

### 3.3 Edit and Optimize
| ID | Tool | Expected output | Priority |
| --- | --- | --- | --- |
| EDT-01 | Compress PDF | Tunable compression with quality and size report | MVP |
| EDT-02 | Edit PDF | Annotations, added text/images/shapes | Phase 2 |
| EDT-03 | Watermark | Text/image watermark with position/opacity options | MVP |
| EDT-04 | Scan to PDF | Camera capture, crop, perspective correction | Mobile phase |
| EDT-05 | OCR PDF | Searchable PDF with recognized text layer | Phase 2 |
| EDT-06 | Compare PDF | Visual/text difference report | Phase 3 |
| EDT-07 | PDF Forms | Detect, create, fill and export interactive forms | Phase 3 |

### 3.4 Security and Signing
| ID | Tool | Expected output | Priority |
| --- | --- | --- | --- |
| SEC-01 | Protect PDF | Password-encrypted PDF | MVP |
| SEC-02 | Unlock PDF | Authorized decryption using a valid password or legitimate permissions | MVP |
| SEC-03 | Redact PDF | Permanently removed content; verified no recoverable underlying text | Phase 2 |
| SEC-04 | Sign PDF | Placed signature or cryptographic signature as distinct options | Phase 3 |
| SEC-05 | Request signatures | Recipient, consent, identity, audit and legal validation | Phase 4 |

### 3.5 Intelligence
| ID | Tool | Expected output | Priority |
| --- | --- | --- | --- |
| AI-01 | Summarize PDF | Grounded document summary with page references | Phase 3 |
| AI-02 | Translate PDF | Translation with best-effort layout preservation | Phase 3 |
| AI-03 | Ask PDF | Source-grounded question answering | Phase 3 |
| AI-04 | Extract Structured Data | JSON/CSV reviewable by a user | Phase 3 |
| AI-05 | Search Across Documents | Private authorized searchable index | Phase 4 |

### 3.6 Workflows, Accounts and Business
| ID | Capability | Priority |
| --- | --- | --- |
| ACC-01 | Guest processing | MVP |
| ACC-02 | Email verification, login, recovery | MVP |
| ACC-03 | Dashboard, favorites, recent jobs (metadata only by default) | MVP |
| WF-01 | Compose reusable tool workflows | Phase 3 |
| WF-02 | Batch files, queues, retries, run history | Phase 3 |
| BIZ-01 | Billing/usage entitlements | Phase 4 |
| BIZ-02 | Team workspaces and roles | Phase 4 |
| BIZ-03 | Developer API and API keys | Phase 4 |
| BIZ-04 | Enterprise controls/audit | Phase 4 |
| APP-01 | Android and iOS apps | Mobile phase |
| APP-02 | Offline desktop app (Linux, Windows, macOS) | Desktop phase |

## 4. Information architecture

Top navigation: Logo | All Tools | Organize | Convert | Edit | Security | AI Tools | Workflows | Pricing | Log In | Sign Up.

Routes:
- `/` — homepage with search, upload and featured tools.
- `/tools` — searchable, filterable complete tool directory.
- `/tools/[slug]` — dedicated tool page with instructions, file picker, settings, preview, progress and download.
- `/workflows` and `/workflows/[id]` — workflow builder and runs.
- `/dashboard` — account workspace (never imply uploaded content is retained unless opt-in).
- `/pricing`, `/login`, `/signup`, `/settings`, `/privacy`, `/terms`.
- `/business`, `/developers`, `/help`.

The core tool UX: select tool -> upload/drag-and-drop -> inspect pages and options -> process -> verify preview/summary -> download/delete.

## 5. Technology and deployment proposal

- **Web:** Next.js + TypeScript + Tailwind CSS + accessible components. Use PDF.js for browser preview. Evaluate pdf-lib or equivalent for selected client-side transformations.
- **Backend API:** Python FastAPI with typed request/response validation and explicit task states.
- **Processing engines:** qpdf for structure, security and page operations; proven Python libraries for remaining operations; LibreOffice in a quarantined conversion container for office-format export; OCRmyPDF/Tesseract for OCR subject to transitive licensing review; a rendering backend for visual previews. Assess tool licenses before adoption.
- **Queue:** Redis-backed background jobs for time-consuming processing; explicit per-tool CPU/time/memory limits and bounded retry policies.
- **Database:** PostgreSQL (accounts, job metadata, billing and workflow definitions; not PDF contents by default).
- **Temporary file storage:** Private encrypted object storage or isolated ephemeral local storage; signed short-lived result URLs. No public bucket access.
- **Mobile:** Flutter for Android/iOS; shared API contracts and native scanning.
- **Desktop:** evaluate Tauri or Flutter Desktop with a local processing bundle; verify offline feature support and licensing per platform.
- **Observability:** redacted logs, request IDs, safe job metrics; never record document text or passwords in telemetry.

Suggested monorepo:

```text
VAILABLE/
├── apps/
│   ├── web/
│   ├── mobile/
│   └── desktop/
├── services/
│   ├── api/
│   ├── pdf-worker/
│   └── intelligence-worker/
├── packages/
│   ├── tool-registry/
│   ├── ui/
│   ├── types/
│   └── api-client/
├── infrastructure/
│   ├── docker/
│   └── deployment/
├── tests/
│   ├── fixtures/
│   ├── e2e/
│   ├── security/
│   └── fidelity/
├── docs/
│   ├── architecture/
│   ├── product/
│   ├── security/
│   └── runbooks/
└── engineering/
    ├── MILESTONES.md
    └── RELEASE_GATES.md
```

## 6. Secure document handling — non-negotiable

1. Apply strict upload size limits, content-type/magic-byte verification and safe extension handling.
2. Reject suspicious archives, extreme page-count/resource bombs, invalid object graphs and malicious embedded payloads.
3. Execute converters in isolated sandboxes as non-root with no unnecessary network access; memory/CPU/time quotas and output limits.
4. Prevent SSRF for URL-to-PDF: deny private, loopback and link-local IP ranges, restrict redirects, validate DNS at connection, and use separate network policy.
5. Isolate files and jobs across users/tenants; random opaque identifiers and scoped download tokens.
6. Encrypt sensitive data in transit and at rest; never log PDF passwords, document content or signature secrets.
7. Set a short automatic deletion policy for guest jobs with manual immediate deletion; implement and test expiry before advertising a retention period.
8. Redaction must erase underlying text/vector/image data as applicable, not merely place a black box; tests attempt re-extraction and inspect metadata/attachments.
9. Password removal only for a PDF uploaded by an authorized user with applicable credentials or permissions; no promise to bypass encryption.
10. E-signature claims must distinguish decorative signatures from certificate-backed digital signatures and comply with applicable jurisdictions.
11. AI processing needs document owner consent, clear data-flow disclosures and strong tenant isolation; grounded answers are not guaranteed to be error-free.
12. Establish license bill of materials and review all third-party dependencies, fonts, models and datasets.

## 7. Delivery phases

### Phase 0 — Foundation (VAI-001)
- Original branding and design tokens, app shell, tools catalog from a typed registry.
- Monorepo setup, lint/typecheck/test pipelines, Docker dev environment, threat model and licensing register.
- Home, tool pages, responsive sidebar/header, document upload UI mock, account wireframes.
- No public launch or false claims of processing functionality.

### Phase 1 — Functional core (VAI-002 onward)
- Merge, Split, Rotate, Organize, JPG to PDF, PDF to JPG, Watermark, basic Compress, Protect and authorized Unlock.
- Guest processing, progress and errors, preview, download, file cleanup, lifecycle tests.
- Basic email-based accounts and dashboard.

### Phase 2 — Professional tools
- DOCX/XLSX/PPTX to PDF, PDF to DOCX, crop/page numbers, annotations, OCR, redaction and best-effort repair.
- Fidelity tests and exception/safety hardening.

### Phase 3 — Intelligence and workflows
- PDF to Markdown, AI summary/translation/Q&A, table export, compare, forms, PDF/A, HTML capture and workflow engine.
- Opt-in AI governance, model-cost budgets, detailed processing reports.

### Phase 4 — Business and clients
- Signature requests with audit trail, paid plans, business API, teams, mobile camera scanner, offline desktop.
- Add production reliability, backup/recovery, availability and commercial safeguards.

## 8. MVP acceptance criteria

- Anonymous user can merge, split, rotate and convert supported files using real processing, not mocks.
- All requested tools are discoverable, but incomplete tools are visibly marked **Coming Soon**, not falsely advertised as operational.
- Each successful job has correct pages, openable output and safe naming.
- Failed jobs give clear errors and do not leak documents or incomplete downloads.
- No job can access another user's file; expiry cleanup is proven by tests.
- Adversarial and corrupted files do not escape sandbox or exhaust the service.
- Tests cover page order, orientation, metadata handling, encrypted PDFs, zero/large files, different scripts/fonts and image quality.
- Web experience works on desktop and small mobile viewports and supports keyboard navigation.
- Dependencies have documented licenses and no unresolved critical security vulnerabilities.

## 9. Product/business boundaries

- Core free suite can be planned, but sustainable pricing and quotas need capacity testing, especially for OCR, Office conversion, AI and bulk processing.
- Do not claim ‘100% accurate’ office conversion, perfect translation format preservation, guaranteed PDF repair, universal free unlimited usage or certified electronic signatures unless demonstrated and legally supported.
- The name VAILABLE, domains and trademarks require availability checks in target markets before public launch; this blueprint is not a clearance opinion.
- No ownership, authorization, brand affiliation or license is implied from the reference competitor site.

## 10. First engineering milestone

**VAI-001: Product foundation and tool registry.** Produce an original responsive homepage and searchable tools catalog, scaffold monorepo and API/worker, define job states, create security threat model, and wire a first authentic Merge PDF happy-path + tests in isolated local development. Do not commit/deploy to any user repository unless repository ownership and location are confirmed.

References for technical evaluation: qpdf GitHub, Mozilla PDF.js, OCRmyPDF, PyMuPDF official license policy; each dependency's transitive obligations require confirmation during implementation.
