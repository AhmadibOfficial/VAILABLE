"""Canonical typed capability registry, shared by API and server-rendered web UI."""
from dataclasses import asdict, dataclass
from typing import Literal

Status = Literal['available', 'coming-soon']

@dataclass(frozen=True)
class Tool:
    id: str
    slug: str
    name: str
    category: str
    output: str
    priority: str
    status: Status = 'coming-soon'


def _load() -> tuple[Tool, ...]:
    # Explicit product data: no runtime dependence on planning documents.
    groups = {
        'Organize': [('ORG-01','Merge PDF','Ordered combined PDF','MVP'),('ORG-02','Split PDF','Individual PDFs or selected ranges','MVP'),('ORG-03','Organize Pages','Reorder, delete and insert pages','MVP'),('ORG-04','Rotate PDF','Rotate PDF pages','MVP'),('ORG-05','Crop PDF','Adjust page crop regions','Phase 2'),('ORG-06','Page Numbers','Place page numbers','Phase 2'),('ORG-07','Repair PDF','Best-effort recovery; some material may be unrecoverable','Phase 2')],
        'Convert': [('CNV-01','PDF to Word','Editable DOCX; layout fidelity varies','Phase 2'),('CNV-02','PDF to PowerPoint','Editable PPTX where feasible','Phase 3'),('CNV-03','PDF to Excel','Review extracted tables as XLSX or CSV','Phase 3'),('CNV-04','Word to PDF','PDF export; layout and fonts may vary','Phase 2'),('CNV-05','PowerPoint to PDF','PDF export; layout and fonts may vary','Phase 2'),('CNV-06','Excel to PDF','Select sheets and page scaling','Phase 2'),('CNV-07','PDF to JPG','Page images or embedded image extraction','MVP'),('CNV-08','JPG/Images to PDF','Ordered images with page size and margins','MVP'),('CNV-09','HTML to PDF','Sandboxed HTML capture','Phase 3'),('CNV-10','PDF to PDF/A','Validated archival PDF','Phase 3'),('CNV-11','PDF to Markdown','Best-effort structured text extraction','Phase 3')],
        'Edit': [('EDT-01','Compress PDF','Compression with quality and size report','MVP'),('EDT-02','Edit PDF','Add annotations, text, images and shapes','Phase 2'),('EDT-03','Watermark','Position text or image watermarks','MVP'),('EDT-04','Scan to PDF','Camera capture and perspective correction','Mobile phase'),('EDT-05','OCR PDF','Searchable text layer; recognition may contain errors','Phase 2'),('EDT-06','Compare PDF','Visual and text difference report','Phase 3'),('EDT-07','PDF Forms','Detect, create, fill and export forms','Phase 3')],
        'Security': [('SEC-01','Protect PDF','Password-encrypted PDF','MVP'),('SEC-02','Unlock PDF','Authorized decryption with valid credentials','MVP'),('SEC-03','Redact PDF','Verified permanent content removal','Phase 2'),('SEC-04','Sign PDF','Placed or cryptographic signatures as distinct options','Phase 3'),('SEC-05','Request signatures','Consent, identity and audit trail; legal validation required','Phase 4')],
        'Intelligence': [('AI-01','Summarize PDF','Grounded summary with page references','Phase 3'),('AI-02','Translate PDF','Translation with best-effort layout preservation','Phase 3'),('AI-03','Ask PDF','Source-grounded answers; review for errors','Phase 3'),('AI-04','Extract Structured Data','Reviewable JSON or CSV','Phase 3'),('AI-05','Search Across Documents','Private authorized search index','Phase 4')],
        'Accounts & workflows': [('ACC-01','Guest processing','Merge without an account','MVP'),('ACC-02','Email verification, login, recovery','Account access','MVP'),('ACC-03','Dashboard, favorites, recent jobs','Metadata by default','MVP'),('WF-01','Compose reusable tool workflows','Reusable processing steps','Phase 3'),('WF-02','Batch files, queues, retries, run history','Batch processing','Phase 3'),('BIZ-01','Billing/usage entitlements','Usage and billing controls','Phase 4'),('BIZ-02','Team workspaces and roles','Shared workspaces','Phase 4'),('BIZ-03','Developer API and API keys','Authenticated developer access','Phase 4'),('BIZ-04','Enterprise controls/audit','Organization controls','Phase 4'),('APP-01','Android and iOS apps','Mobile applications','Mobile phase'),('APP-02','Offline desktop app (Linux, Windows, macOS)','Offline desktop application','Desktop phase')],
    }
    import re
    return tuple(Tool(id, re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-'), name, category, output, priority,
                      'available' if id in ('ORG-01','ACC-01') else 'coming-soon')
                 for category, rows in groups.items() for id, name, output, priority in rows)

TOOLS = _load()

def serialized() -> list[dict]:
    return [asdict(tool) for tool in TOOLS]
