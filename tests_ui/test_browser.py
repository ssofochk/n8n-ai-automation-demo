import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='session')
def server():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'src.api:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urlopen(url, timeout=1): break
            except OSError: time.sleep(.1)
        else: raise RuntimeError('Server did not start')
        yield url
    finally:
        process.terminate(); process.wait(timeout=10)

@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as p:
        executable = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
        b = p.chromium.launch(executable_path=executable or None, args=['--no-sandbox'])
        yield b
        b.close()

@pytest.fixture
def page(browser, server):
    p = browser.new_page(viewport={'width': 1100, 'height': 850})
    p.goto(server)
    yield p
    p.close()

def fill(page, a='24', b='5', op='multiply'):
    page.get_by_label('First number').fill(a)
    page.get_by_label('Second number').fill(b)
    page.locator(f'label[for={op}]').click()

def test_initial_and_operations(page):
    expect(page.get_by_role('heading', name='Your result')).to_be_visible()
    expect(page.get_by_text('Nothing here yet!')).to_be_visible()
    for op in ['add','subtract','multiply','divide']:
        page.locator(f'label[for={op}]').click()
        expect(page.locator(f'#{op}')).to_be_checked()
    expect(page.get_by_role('button', name='Calculate ♡')).to_be_enabled()

def test_success_mock_full_flow(page):
    requests = []
    def reply(route):
        requests.append(route.request.post_data_json)
        route.fulfill(json={'result':120})
    page.route('**/api/calculate', reply)
    fill(page)
    page.get_by_role('button', name='Calculate ♡').click()
    expect(page.get_by_text('24 × 5 = 120', exact=True)).to_be_visible()
    expect(page.locator('.result-value')).to_have_text('120')
    assert requests == [{'a':24,'b':5,'operation':'multiply'}]

def test_required_and_invalid(page):
    calls = []
    page.route('**/api/calculate', lambda route: (calls.append(1), route.abort()))
    page.get_by_role('button', name='Calculate ♡').click()
    expect(page.locator('#a-error')).to_have_text('Please enter a number.')
    expect(page.locator('#b-error')).to_be_visible()
    expect(page.locator('#a')).to_be_focused()
    fill(page, 'abc', '2')
    page.get_by_role('button', name='Calculate ♡').click()
    expect(page.locator('#a-error')).to_have_text('Please enter a valid number.')
    expect(page.locator('#a-error')).to_be_visible()
    assert not calls

def test_loading_and_duplicate(page):
    routes = []
    page.route('**/api/calculate', lambda route: routes.append(route))
    fill(page)
    page.get_by_role('button', name='Calculate ♡').click()
    expect(page.get_by_text('Calculating your answer…')).to_be_visible()
    expect(page.locator('#submit')).to_be_disabled()
    page.locator('#submit').dispatch_event('click')
    page.locator('#b').press('Enter')
    page.locator('#calculator').evaluate('(form) => { form.requestSubmit(); form.requestSubmit(); }')
    page.wait_for_timeout(200)
    assert len(routes) == 1
    routes[0].fulfill(json={'result':120})
    expect(page.locator('.result-value')).to_have_text('120')
    expect(page.locator('#submit')).to_be_enabled()

def test_empty_response(page):
    page.route('**/api/calculate', lambda route: route.fulfill(status=204))
    fill(page); page.locator('#submit').click()
    expect(page.get_by_text('No result returned. Please try again.')).to_be_visible()
    expect(page.locator('#submit')).to_be_enabled()

def test_error_and_retry(page):
    page.route('**/api/calculate', lambda route: route.fulfill(status=500, json={'detail':'Internal error'}))
    fill(page); page.locator('#submit').click()
    expect(page.get_by_role('alert')).to_have_text('Something went wrong. Please try again.')
    page.unroute('**/api/calculate')
    page.route('**/api/calculate', lambda route: route.fulfill(json={'result':120}))
    page.locator('#submit').click()
    expect(page.locator('.result-value')).to_have_text('120')
    expect(page.get_by_role('alert')).to_have_count(0)

def test_real_api_keyboard_and_mobile(page):
    page.set_viewport_size({'width':375,'height':812})
    page.keyboard.press('Tab')
    expect(page.locator('#a')).to_be_focused()
    assert page.locator('#a').evaluate('(e) => getComputedStyle(e).outlineStyle') == 'solid'
    page.keyboard.type('8'); page.keyboard.press('Tab'); page.keyboard.press('ArrowRight'); page.keyboard.press('ArrowRight'); page.keyboard.press('ArrowRight')
    expect(page.locator('#divide')).to_be_checked()
    page.keyboard.press('Tab'); page.keyboard.type('2'); page.keyboard.press('Enter')
    expect(page.get_by_text('8 ÷ 2 = 4', exact=True)).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')

def test_real_division_error(page):
    fill(page,'8','0','divide'); page.locator('#submit').click()
    expect(page.get_by_role('alert')).to_have_text('Cannot divide by zero')
    page.locator('#b').fill('2'); page.locator('#submit').click()
    expect(page.locator('.result-value')).to_have_text('4')
