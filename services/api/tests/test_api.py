import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
import tempfile

import pytest
import asyncio
import httpx
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, TextStringObject

from packages.tool_registry import TOOLS
from services.api import app as api
from services.api.worker import merge

class LocalClient:
    def request(self, method, path, **kwargs):
        async def send():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app), base_url='http://test') as client:
                return await client.request(method, path, **kwargs)
        return asyncio.run(send())

    def get(self, path, **kwargs):
        return self.request('GET', path, **kwargs)

    def post(self, path, **kwargs):
        return self.request('POST', path, **kwargs)

client = LocalClient()


def pdf(labels=('A',), encrypted=False, active=False):
    writer = PdfWriter()
    for index, label in enumerate(labels):
        page = writer.add_blank_page(width=200 + index, height=300)
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 10 100 Td ({label}) Tj ET'.encode())
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})})})
        page[NameObject('/Contents')] = writer._add_object(stream)
    writer.add_metadata({'/Title': 'PRIVATE synthetic metadata'})
    if encrypted:
        writer.encrypt('synthetic-password')
    if active:
        writer.add_js('app.alert("synthetic")')
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def upload(*payloads, name='input.pdf', mime='application/pdf'):
    return client.post('/api/merge', files=[('files', (name, data, mime)) for data in payloads])


def texts(data):
    return [page.extract_text() for page in PdfReader(io.BytesIO(data)).pages]


def test_registry_complete_and_honest():
    blueprint = (api.ROOT / 'docs/product/BLUEPRINT.md').read_text()
    expected = set(re.findall(r'\| ((?:ORG|CNV|EDT|SEC|AI|ACC|WF|BIZ|APP)-\d+) \|', blueprint))
    assert {t.id for t in TOOLS} == expected
    assert len({t.slug for t in TOOLS}) == len(TOOLS) == len(expected)
    assert {t.id for t in TOOLS if t.status == 'available'} == {'ORG-01', 'ACC-01'}
    assert client.get('/api/tools').json()[0]['id'] == 'ORG-01'
    for tool in TOOLS:
        response = client.get('/tools/' + tool.slug)
        assert response.status_code == 200
        if tool.status == 'coming-soon':
            assert 'Coming Soon' in response.text
            assert 'type="file"' not in response.text
    assert client.get('/tools/missing').status_code == 404


def test_merge_real_page_order_and_metadata():
    response = upload(pdf(('first', 'second')), pdf(('third',)))
    assert response.status_code == 200, response.text
    assert texts(response.content) == ['first', 'second', 'third']
    reader = PdfReader(io.BytesIO(response.content), strict=True)
    assert [int(p.mediabox.width) for p in reader.pages] == [200, 201, 200]
    assert '/Title' not in reader.metadata
    assert response.headers['content-type'] == 'application/pdf'
    assert response.headers['content-disposition'] == 'attachment; filename="vailable-merged.pdf"'
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'


@pytest.mark.parametrize('bad,code', [(b'',415),(b'not a pdf',415),(b'%PDF-1.7\ntruncated',422),(pdf(encrypted=True),422),(pdf(active=True),422),(pdf(()),422)])
def test_invalid_encrypted_and_active_fail_closed(bad, code):
    response = upload(pdf(), bad)
    assert response.status_code == code
    assert response.headers['content-type'].startswith('application/json')
    assert 'content-disposition' not in response.headers
    assert 'PRIVATE' not in response.text


@pytest.mark.parametrize('count', [0, 1, 11])
def test_file_counts(count):
    assert upload(*([pdf()] * count)).status_code == 400


@pytest.mark.parametrize('name,mime', [('fake.txt','application/pdf'),('fake.pdf','text/plain')])
def test_type_checks(name, mime):
    assert upload(pdf(),pdf(),name=name,mime=mime).status_code == 415


def test_size_limits(monkeypatch):
    monkeypatch.setattr(api, 'MAX_FILE', 100)
    assert upload(pdf(),pdf()).status_code == 413
    monkeypatch.setattr(api, 'MAX_BODY', 100)
    assert upload(pdf(),pdf()).status_code == 413


def test_extra_field_rejected():
    response = client.post('/api/merge', data={'unexpected':'x'}, files=[('files',('a.pdf',pdf(),'application/pdf'))]*2)
    assert response.status_code == 400


def test_page_limit(tmp_path):
    path = tmp_path / 'synthetic.pdf'
    path.write_bytes(pdf(tuple('page' for _ in range(301))))
    with pytest.raises(ValueError, match='300'):
        merge([path])


def test_output_limit(tmp_path, monkeypatch):
    from services.api import worker
    path = tmp_path / 'synthetic.pdf'
    path.write_bytes(pdf())
    monkeypatch.setattr(worker, 'MAX_OUTPUT', 1)
    with pytest.raises(ValueError, match='output exceeds'):
        merge([path])


def test_job_cleanup_and_safe_names(monkeypatch, tmp_path):
    original = tempfile.TemporaryDirectory
    monkeypatch.setattr(api.tempfile, 'TemporaryDirectory', lambda **kw: original(dir=tmp_path, **kw))
    for data in (pdf(), b'%PDF-broken'):
        upload(pdf(), data, name='../../outside.pdf')
        assert list(tmp_path.iterdir()) == []


def test_timeout_cleanup(monkeypatch, tmp_path):
    original = tempfile.TemporaryDirectory
    monkeypatch.setattr(api.tempfile, 'TemporaryDirectory', lambda **kw: original(dir=tmp_path, **kw))
    monkeypatch.setattr(api, 'PROCESS_SECONDS', 0)
    assert upload(pdf(),pdf()).status_code == 422
    assert list(tmp_path.iterdir()) == []


def test_busy_and_recovery():
    api.SLOTS.acquire()
    api.SLOTS.acquire()
    try:
        assert upload(pdf(),pdf()).status_code == 503
    finally:
        api.SLOTS.release()
        api.SLOTS.release()
    assert upload(pdf(),pdf()).status_code == 200


def test_concurrent_jobs_are_isolated():
    def job(label):
        response = upload(pdf((label,)), pdf((label + '2',)))
        assert response.status_code == 200
        return texts(response.content)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(job, ['left', 'right'])) == [['left','left2'],['right','right2']]


def test_malformed_multipart():
    response = client.post('/api/merge', content=b'broken', headers={'content-type':'multipart/form-data; boundary=x'})
    assert response.status_code == 400


def test_active_page_rejected(tmp_path):
    writer = PdfWriter()
    page = writer.add_blank_page(200,300)
    page[NameObject('/AA')] = DictionaryObject({NameObject('/O'): DictionaryObject({NameObject('/S'):NameObject('/JavaScript'),NameObject('/JS'):TextStringObject('alert(1)')})})
    path = tmp_path / 'active.pdf'
    with path.open('wb') as out:
        writer.write(out)
    with pytest.raises(ValueError, match='Interactive'):
        merge([path])


def test_worker_cancellation_kills_reaps_and_cleans(monkeypatch, tmp_path):
    original = tempfile.TemporaryDirectory
    monkeypatch.setattr(api.tempfile, 'TemporaryDirectory', lambda **kw: original(dir=tmp_path, **kw))
    class Child:
        returncode = None
        killed = False
        reaped = False
        def poll(self):
            return self.returncode
        def kill(self):
            self.killed = True
            self.returncode = -9
        def wait(self):
            self.reaped = True
            return self.returncode
    child = Child()
    monkeypatch.setattr(api.subprocess, 'Popen', lambda *a, **kw: child)
    async def cancel():
        task = asyncio.create_task(api.process([pdf(), pdf()]))
        await asyncio.sleep(.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(cancel())
    assert child.killed and child.reaped
    assert list(tmp_path.iterdir()) == []


def test_worker_resource_failure_is_generic(monkeypatch):
    class Child:
        returncode = -9
        def poll(self):
            return self.returncode
        def wait(self):
            return self.returncode
    monkeypatch.setattr(api.subprocess, 'Popen', lambda *a, **kw: Child())
    response = upload(pdf(), pdf())
    assert response.status_code == 422
    assert response.json()['detail'] == 'PDF processing exceeded resource limits.'


def test_upload_timeout_releases_capacity(monkeypatch):
    original = api.read_bounded
    async def stalled(request):
        raise TimeoutError
    monkeypatch.setattr(api, 'read_bounded', stalled)
    assert upload(pdf(), pdf()).status_code == 408
    monkeypatch.setattr(api, 'read_bounded', original)
    assert upload(pdf(), pdf()).status_code == 200


def test_ten_files_preserve_order():
    response = upload(*(pdf((str(i),)) for i in range(10)))
    assert response.status_code == 200
    assert texts(response.content) == [str(i) for i in range(10)]
