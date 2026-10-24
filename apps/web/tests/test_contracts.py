"""Check server-rendered frontend contracts without opening a network socket."""
from html.parser import HTMLParser
from pathlib import Path

from services.api.app import app, WEB
from services.api.tests.test_api import client


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)

    def by_id(self, identifier):
        return next(attrs for _, attrs in self.elements if attrs.get('id') == identifier)


def test_catalog_links_categories_and_badges_match_api():
    response = client.get('/tools')
    assert response.status_code == 200
    tools = client.get('/api/tools').json()
    document = Document(response.text)
    cards = [attrs for tag, attrs in document.elements if tag == 'article']
    assert len(cards) == len(tools)
    links = {attrs.get('href') for tag, attrs in document.elements if tag == 'a'}
    for card, tool in zip(cards, tools, strict=True):
        assert card['data-category'] == tool['category']
        assert card['data-search'] == f"{tool['name']} {tool['output']} {tool['category']}".lower()
        assert '/tools/' + tool['slug'] in links
    badges = [attrs['class'] for tag, attrs in document.elements
              if tag == 'span' and attrs.get('class', '').startswith('badge ')]
    assert badges == ['badge ' + tool['status'] for tool in tools]
    assert document.by_id('results')['aria-live'] == 'polite'
    assert ('a', {'class': 'skip', 'href': '#main'}) in document.elements


def test_all_incomplete_tools_are_coming_soon_without_uploads():
    for tool in client.get('/api/tools').json():
        if tool['status'] == 'available':
            continue
        response = client.get('/tools/' + tool['slug'])
        assert response.status_code == 200
        document = Document(response.text)
        assert 'Coming Soon' in document.text
        assert tool['name'] in document.text
        assert not any(tag in ('input', 'form') for tag, _ in document.elements)


def test_merge_page_loads_assets_and_accessible_controls():
    response = client.get('/tools/merge-pdf')
    assert response.status_code == 200
    document = Document(response.text)
    picker = document.by_id('files')
    assert picker['name'] == 'files'
    assert picker['type'] == 'file'
    assert picker['accept'] == '.pdf,application/pdf'
    assert 'multiple' in picker
    assert picker['aria-describedby'] == 'limits'
    assert 'disabled' in document.by_id('merge-button')
    assert document.by_id('merge-status')['role'] == 'status'
    assert document.by_id('download')['download'] == 'vailable-merged.pdf'
    assert 'hidden' in document.by_id('download')
    assert ('script', {'src': '/assets/app.js', 'defer': None}) in document.elements
    assert ('link', {'rel': 'stylesheet', 'href': '/assets/style.css'}) in document.elements
    assets = next(route for route in app.routes if route.path == '/assets')
    assert Path(assets.app.directory) == WEB
    for filename in ('app.js', 'style.css'):
        assert (WEB / filename).read_text().strip()
