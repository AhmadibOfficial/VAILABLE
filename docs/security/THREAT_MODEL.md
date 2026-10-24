# Initial threat model

Trust boundaries: browser -> upload API -> temporary isolated job directory -> PDF parser / conversion worker -> private output -> scoped download.

Threats to test: fake file extensions, malformed/encrypted PDFs, decompression bombs, path traversal, parser memory exhaustion, cross-job/cross-tenant access, document remnants, untrusted macros, SSRF from HTML-to-PDF, AI prompt injection, unauthorized password removal, false/overlay-only redaction, e-signature impersonation.

Before public upload access: isolate worker with non-root UID, no network by default, page/file/time/memory/output quotas; enforce cleanup and test denial of unauthorized access. Never use real user PDFs in automated tests.
