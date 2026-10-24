"""Local VAI-001 application. Run from repository root with uvicorn."""
import asyncio
from html import escape
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response, FileResponse
from starlette.datastructures import UploadFile
from packages.tool_registry import TOOLS, serialized

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'apps/web'
MAX_FILE = 5 * 1024**2
MAX_BODY = 20 * 1024**2
PROCESS_SECONDS = 12
SLOTS = threading.BoundedSemaphore(2)
app = FastAPI(title='VAILABLE local foundation', docs_url=None, redoc_url=None, openapi_url=None)
# Serve only browser assets. A directory mount exposes package manifests and test code.
PUBLIC_ASSETS = {'app.js': 'text/javascript', 'style.css': 'text/css'}


@app.get('/assets/{name}', include_in_schema=False)
async def public_asset(name: str):
    media_type = PUBLIC_ASSETS.get(name)
    if media_type is None:
        raise HTTPException(404, 'Asset not found.')
    return FileResponse(WEB / name, media_type=media_type)



@app.middleware('http')
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
        'Cross-Origin-Resource-Policy': 'same-origin', 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"})
    return response


@app.get('/api/tools')
async def tools():
    return serialized()


def render(content: str, title='Document tools'):
    return HTMLResponse((WEB / 'shell.html').read_text().replace('{{title}}', escape(title)).replace('{{content}}', content))


@app.get('/', response_class=HTMLResponse)
@app.get('/tools', response_class=HTMLResponse)
async def catalog(request: Request):
    cards = ''.join(f'<article class="card" data-search="{escape((t.name + " " + t.output + " " + t.category).lower())}" data-category="{escape(t.category)}"><div class="card-top"><span class="tool-id">{t.id}</span><span class="badge {t.status}">{"Available" if t.status == "available" else "Coming Soon"}</span></div><h3><a href="/tools/{t.slug}">{escape(t.name)}</a></h3><p>{escape(t.output)}</p></article>' for t in TOOLS)
    options = ''.join(f'<option>{escape(c)}</option>' for c in dict.fromkeys(t.category for t in TOOLS))
    return render(f'''<section class="hero"><p class="eyebrow">A little order. A lot of possibility.</p><h1>Your next chapter,<br>minus the paperwork.</h1><p class="intro">A clear place to work with documents. Start with PDF merging, or explore what’s taking shape.</p><a class="button" href="/tools/merge-pdf">Merge your PDFs <span aria-hidden="true">↗</span></a><p class="small">Local development foundation · No account needed for merge</p></section><section aria-labelledby="catalog-title"><div class="section-heading"><div><p class="eyebrow">The document workbench</p><h2 id="catalog-title">Find your tool</h2></div><p>One working tool. A clearly marked roadmap.</p></div><form role="search" id="search-form"><div><label for="search">Search tools</label><input id="search" type="search" placeholder="Try merge, images, or signatures"></div><div><label for="category">Category</label><select id="category"><option value="">All categories</option>{options}</select></div></form><p id="results" role="status" aria-live="polite">{len(TOOLS)} capabilities</p><div class="grid">{cards}</div><p id="empty" hidden>No tools match. Try another search or category.</p></section>''')


@app.get('/tools/{slug}', response_class=HTMLResponse)
async def tool_page(slug: str):
    tool = next((t for t in TOOLS if t.slug == slug), None)
    if not tool:
        raise HTTPException(404, 'Tool not found.')
    if tool.id == 'ACC-01':
        return render('<h1>Guest processing</h1><p>Merge PDFs without an account.</p><a class="button" href="/tools/merge-pdf">Open Merge PDF</a>')
    if tool.id != 'ORG-01':
        return render(f'<section class="hero"><span class="badge">Coming Soon</span><h1>{escape(tool.name)}</h1><p>{escape(tool.output)}</p><p>This capability is planned and cannot process documents yet.</p><a href="/tools">Explore all tools</a></section>', tool.name)
    return render('''<section class="merge-panel"><a href="/tools">← All tools</a><p class="eyebrow">Organize / Merge PDF</p><h1>Bring it all together.</h1><p>Combine 2–10 PDFs in the order below. Pages keep their original order within each file.</p><p id="limits">5 MiB per file · 20 MiB request · 300 total pages · 25 MiB output. Encrypted, interactive and attached-content PDFs are rejected.</p><noscript><p>Enable JavaScript to select, order and merge PDFs.</p></noscript><form id="merge-form"><label class="upload" for="files">Choose PDFs<input id="files" name="files" type="file" accept=".pdf,application/pdf" multiple required aria-describedby="limits"></label><p>Use Move up / Move down to set file order before merging.</p><ol id="file-list"></ol><button id="merge-button" type="submit" disabled>Merge PDFs</button></form><p id="merge-status" role="status" aria-live="polite"></p><a id="download" class="button" hidden download="vailable-merged.pdf">Download merged PDF</a><p class="small">Files are sent to this local server. Temporary job files are cleaned up after processing; there is no saved history. Browser downloads remain on your device. Merging does not preserve document-level bookmarks, forms, signatures or metadata. Review the result before relying on it.</p></section>''', 'Merge PDF')


async def read_bounded(request):
    # Reject obviously oversized uploads before consuming request-body memory.
    advertised = request.headers.get('content-length')
    if advertised is not None:
        try:
            declared = int(advertised)
        except (ValueError, TypeError):
            raise HTTPException(400, 'Invalid Content-Length.')
        if declared < 0:
            raise HTTPException(400, 'Invalid Content-Length.')
        if declared > MAX_BODY:
            raise HTTPException(413, 'Request exceeds 20 MiB.')
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_BODY:
            raise HTTPException(413, 'Request exceeds 20 MiB.')
    request._body = bytes(body)


async def process(payloads):
    with tempfile.TemporaryDirectory(prefix='vailable-') as directory:
        paths = []
        for index, data in enumerate(payloads):
            path = Path(directory) / f'{index}.pdf'
            path.write_bytes(data)
            paths.append(str(path))
        with tempfile.TemporaryFile() as output:
            child = subprocess.Popen([sys.executable, str(Path(__file__).with_name('worker.py')), *paths],
                stdout=output, stderr=subprocess.DEVNULL, env={'PATH': '/usr/bin:/bin'}, cwd=directory)
            deadline = time.monotonic() + PROCESS_SECONDS
            try:
                while child.poll() is None:
                    if time.monotonic() >= deadline:
                        raise HTTPException(422, 'PDF processing exceeded time limits.')
                    await asyncio.sleep(.02)
                output.seek(0)
                data = output.read(25 * 1024**2 + 1)
                if child.returncode:
                    message = data.decode('utf-8', errors='replace') if child.returncode == 2 else 'PDF processing exceeded resource limits.'
                    raise HTTPException(422, message)
                if not data.startswith(b'%PDF-') or len(data) > 25 * 1024**2:
                    raise HTTPException(422, 'Invalid or oversized output.')
                return data
            finally:
                if child.poll() is None:
                    child.kill()
                child.wait()


@app.post('/api/merge')
async def merge(request: Request):
    if not SLOTS.acquire(blocking=False):
        raise HTTPException(503, 'Processing capacity reached. Try again shortly.')
    try:
        try:
            await asyncio.wait_for(read_bounded(request), timeout=15)
        except TimeoutError:
            raise HTTPException(408, 'Upload timed out.')
        try:
            async with request.form(max_files=10, max_fields=0, max_part_size=MAX_FILE) as form:
                files = form.getlist('files')
                if len(form.multi_items()) != len(files) or not 2 <= len(files) <= 10 or not all(isinstance(f, UploadFile) for f in files):
                    raise HTTPException(400, 'Choose 2–10 PDF files using the files field.')
                payloads = []
                for file in files:
                    data = await file.read(MAX_FILE + 1)
                    if len(data) > MAX_FILE:
                        raise HTTPException(413, 'Each file must be at most 5 MiB.')
                    if file.content_type != 'application/pdf' or not (file.filename or '').lower().endswith('.pdf') or not data.startswith(b'%PDF-'):
                        raise HTTPException(415, 'Only nonempty PDF files are supported.')
                    payloads.append(data)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(400, 'Invalid multipart upload.')
        result = await process(payloads)
        return Response(result, media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="vailable-merged.pdf"'})
    finally:
        SLOTS.release()
