# Dependency and asset register — VAI-001

No third-party UI, icons, fonts, PDF fixtures or competitor assets were copied.
The interface uses system fonts, text and original CSS. Test PDFs are synthetic.
Dependencies are imported, not vendored; retain the upstream license files and
notices included in their distributions when redistributing an environment.

| Dependency | Purpose | License (distribution metadata) |
| --- | --- | --- |
| FastAPI | HTTP routes and request validation | MIT |
| Starlette | ASGI, multipart and static responses | BSD-3-Clause |
| Uvicorn | Local ASGI server | BSD-3-Clause |
| python-multipart | Multipart parsing | Apache-2.0 |
| pypdf | Static PDF page copying and validation | BSD-3-Clause |
| Pydantic / pydantic-core | FastAPI schema runtime | MIT |
| AnyIO | ASGI concurrency support | MIT |
| HTTPX | In-process integration-test client | BSD-3-Clause |
| pytest | Test runner | MIT |
| Playwright | Browser testing (development only) | Apache-2.0 |
| Chromium | Browser testing (system dependency) | BSD-style and bundled third-party notices |

Direct Python versions are pinned in `services/api/requirements*.txt`. This is
an initial license register, not an exhaustive transitive SBOM or security audit.
A clean environment resolves transitive dependencies within upstream constraints;
produce a resolved lock/SBOM, preserve all transitive notices and complete an
advisory scan before release. No GPL/AGPL conversion engine, OCR engine, PDF.js,
external font, model or dataset is included. No Office conversion fidelity,
PDF/A compliance or digital-signature certification is claimed.

The supplied host currently has Starlette 0.50.0 alongside FastAPI 0.118.0,
outside that FastAPI distribution's declared `<0.49.0` bound. Tests report actual
behavior in that host, but use a fresh venv and the requirements for supported
dependency resolution; do not treat the preinstalled environment as a lockfile.
