"""Frontend contracts checked in Chromium against the actual application."""
import pytest
from playwright.sync_api import expect

from services.api.tests.test_api import pdf


def test_catalog_matches_api_and_unimplemented_pages(browser_app):
    browser, url = browser_app
    page = browser.new_page(viewport={"width": 390, "height": 844})
    try:
        response = page.request.get(url + '/api/tools')
        assert response.ok
        tools = response.json()
        page.goto(url + '/tools')
        expect(page.locator('.card')).to_have_count(len(tools))
        for tool in tools:
            card = page.locator('.card').filter(has=page.get_by_role('link', name=tool['name'], exact=True))
            expect(card.locator('.tool-id')).to_have_text(tool['id'])
            expect(card.locator('h3 a')).to_have_attribute('href', '/tools/' + tool['slug'])
            expect(card.locator('.badge')).to_have_text(
                'Available' if tool['status'] == 'available' else 'Coming Soon')
            expect(card.locator('p')).to_have_text(tool['output'])
        for tool in tools:
            if tool['status'] != 'available':
                page.goto(url + '/tools/' + tool['slug'])
                expect(page.get_by_role('heading', level=1)).to_have_text(tool['name'])
                expect(page.get_by_text('Coming Soon', exact=True)).to_be_visible()
                expect(page.locator('input[type=file], #merge-form')).to_have_count(0)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    finally:
        page.close()


def select_files(page, names):
    page.locator('#files').set_input_files([
        {'name': name, 'mimeType': 'application/pdf', 'buffer': pdf()}
        for name in names
    ])


def test_file_limits_and_validation_prevent_upload(browser_app):
    browser, url = browser_app
    page = browser.new_page()
    requests = []
    page.on('request', lambda request: requests.append(request.url) if '/api/merge' in request.url else None)
    try:
        page.goto(url + '/tools/merge-pdf')
        expect(page.get_by_label('Choose PDFs')).to_have_attribute('aria-describedby', 'limits')
        expect(page.locator('#merge-status')).to_have_attribute('aria-live', 'polite')
        expect(page.locator('#merge-button')).to_be_disabled()
        select_files(page, ['one.pdf'])
        expect(page.locator('#merge-button')).to_be_disabled()
        select_files(page, [f'{index}.pdf' for index in range(11)])
        expect(page.locator('#merge-button')).to_be_disabled()
        expect(page.locator('#merge-status')).to_have_text('Choose at most 10 PDFs.')
        select_files(page, ['one.pdf', 'wrong.txt'])
        page.locator('#merge-button').click()
        expect(page.locator('#merge-status')).to_have_text('Choose nonempty PDFs within the displayed limits.')
        expect(page.locator('#download')).to_be_hidden()
        assert requests == []
    finally:
        page.close()


@pytest.mark.parametrize('failure, message', [
    ('server', 'Processing capacity reached. Try again shortly.'),
    ('network', 'Could not reach the server. Please try again.'),
    ('html', 'Server returned an unexpected response.'),
    ('invalid', 'Server returned an invalid PDF.'),
])
def test_merge_failure_recovers_controls(browser_app, failure, message):
    browser, url = browser_app
    page = browser.new_page()

    def fail(route):
        assert route.request.method == 'POST'
        assert 'multipart/form-data; boundary=' in route.request.headers['content-type']
        if failure == 'network':
            route.abort()
        elif failure == 'server':
            route.fulfill(status=503, json={'detail': message})
        else:
            route.fulfill(content_type='text/html' if failure == 'html' else 'application/pdf', body='invalid')

    try:
        page.route('**/api/merge', fail)
        page.goto(url + '/tools/merge-pdf')
        select_files(page, ['one.pdf', 'two.pdf'])
        page.locator('#merge-button').click()
        expect(page.locator('#merge-status')).to_have_text(message)
        expect(page.locator('#download')).to_be_hidden()
        expect(page.locator('#merge-button')).to_be_enabled()
        expect(page.locator('#files')).to_be_enabled()
        expect(page.get_by_role('button', name='Move down: one.pdf', exact=True)).to_be_enabled()
    finally:
        page.close()
