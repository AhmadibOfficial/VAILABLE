"""Real Chromium checks. No external URLs, assets or document fixtures."""
import io
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest
from playwright.sync_api import sync_playwright, expect
from services.api.tests.test_api import pdf, texts
from services.api.app import ROOT


@pytest.fixture(scope='module')
def browser_app():
    executable = shutil.which('chromium')
    if not executable:
        pytest.fail('Chromium missing: install chromium or set up the documented test environment.')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    server = subprocess.Popen([sys.executable,'-m','uvicorn','services.api.app:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}'
    try:
        for _ in range(100):
            if server.poll() is not None:
                pytest.fail('Local test server exited during startup.')
            try:
                with urlopen(url + '/api/tools', timeout=.2) as response:
                    assert response.status == 200
                break
            except OSError:
                time.sleep(.1)
        else:
            pytest.fail('Local test server did not become ready.')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=executable, headless=True, args=['--no-sandbox'])
            yield browser,url
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)


@pytest.mark.parametrize('width,height',[(390,844),(1440,1000)])
def test_catalog_responsive_search_keyboard(browser_app,width,height):
    browser,url = browser_app
    page = browser.new_page(viewport={'width':width,'height':height})
    try:
        page.goto(url)
        assert page.title() == 'Document tools · VAILABLE'
        page.keyboard.press('Tab')
        expect(page.get_by_text('Skip to content')).to_be_focused()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.locator('#search').fill('merge')
        expect(page.locator('.card:visible')).to_have_count(2)  # Merge and guest processing
        page.locator('#category').select_option(label='Organize')
        expect(page.locator('.card:visible')).to_have_count(1)
        page.locator('#search').fill('no matching capability')
        expect(page.locator('#empty')).to_be_visible()
        page.goto(url + '/tools/pdf-to-word')
        expect(page.get_by_text('Coming Soon',exact=True)).to_be_visible()
        expect(page.locator('input[type=file]')).to_have_count(0)
    finally:
        page.close()


def test_browser_real_merge_order_and_failure(browser_app,tmp_path):
    browser,url = browser_app
    page = browser.new_page(viewport={'width':390,'height':844},accept_downloads=True)
    try:
        page.goto(url + '/tools/merge-pdf')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        expect(page.locator('#download')).to_be_hidden()
        page.locator('#files').set_input_files([
            {'name':'first.pdf','mimeType':'application/pdf','buffer':pdf(('first','second'))},
            {'name':'last.pdf','mimeType':'application/pdf','buffer':pdf(('last',))}])
        page.get_by_role('button',name='Move up: last.pdf',exact=True).click()
        page.get_by_role('button',name='Merge PDFs',exact=True).click()
        expect(page.locator('#download')).to_be_visible(timeout=20000)
        with page.expect_download() as event:
            page.locator('#download').click()
        target = tmp_path / 'download.pdf'
        event.value.save_as(target)
        assert texts(target.read_bytes()) == ['last','first','second']
        page.locator('#files').set_input_files([
            {'name':'bad.pdf','mimeType':'application/pdf','buffer':b'%PDF-broken'},
            {'name':'valid.pdf','mimeType':'application/pdf','buffer':pdf()}])
        expect(page.locator('#download')).to_be_hidden()
        page.get_by_role('button',name='Merge PDFs',exact=True).click()
        expect(page.locator('#merge-status')).to_contain_text('Invalid',timeout=20000)
        expect(page.locator('#download')).to_be_hidden()
    finally:
        page.close()
