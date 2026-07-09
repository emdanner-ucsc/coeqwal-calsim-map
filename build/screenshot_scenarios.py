#!/usr/bin/env python3
"""Headless verification of scenario switching (serves the repo over http).

Usage (after build/sandbox_setup.sh):
  LD_LIBRARY_PATH=$HOME/stublibs PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1 \
    python3 build/screenshot_scenarios.py [outdir]

Checks: picker present in both modes; switching to s0030 (hist) and s0091
(cc95) swaps series (verified against scenarios/*.json), updates WYT strip
and .cursid labels; a USBR Alt3 run (s0098) shows the no-simple notice in
simple mode; switching back to s0020 restores embedded values exactly.
"""
import json, os, sys, threading, functools, http.server
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'shots_scen')
os.makedirs(OUT, exist_ok=True)
PORT = 8471

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
Handler.log_message = lambda *a, **k: None
srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

exp = {sid: json.load(open(os.path.join(ROOT, 'scenarios', sid + '.json')))
       for sid in ('s0020', 's0030', 's0091', 's0098')}

errors = []
def onerr(e): errors.append(str(e))

VENDOR = os.path.join(ROOT, 'build', 'vendor')
def route(r):
    url = r.request.url
    if 'leaflet.min.js' in url or url.endswith('leaflet.js'):
        r.fulfill(path=os.path.join(VENDOR, 'leaflet.js'),
                  content_type='application/javascript')
    elif 'leaflet.min.css' in url or url.endswith('leaflet.css'):
        r.fulfill(path=os.path.join(VENDOR, 'leaflet.css'), content_type='text/css')
    elif 'cartocdn' in url or 'openstreetmap' in url:
        r.abort()
    else:
        r.continue_()

def wait_sid(page, sid):
    page.wait_for_function(
        f"() => document.querySelector('.cursid').textContent === '{sid}'",
        timeout=20000)
    page.wait_for_timeout(400)

def arcq(page, arc, i):
    return page.evaluate(
        f"() => D.arcs.find(a=>a.i==='{arc}').q[{i}]")

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader'])
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.on('pageerror', onerr)
    pg.route('**/*', route)
    pg.goto(f'http://127.0.0.1:{PORT}/CalSim3_water_map.html#detail')
    pg.wait_for_timeout(2500)
    pg.keyboard.press('Escape')   # close the auto-opened about panel
    pg.wait_for_timeout(300)

    assert pg.locator('#scenrow1 select').count() == 1, 'detail picker missing'
    v0 = arcq(pg, 'C_SAC003', 660)
    assert v0 == exp['s0020']['arcs']['C_SAC003'][660], f's0020 embed {v0}'

    # -- switch to 3.1 historical (s0030: no min flows)
    pg.select_option('#scenrow1 select', '3.1')
    wait_sid(pg, 's0030')
    v = arcq(pg, 'C_SAC003', 660)
    assert v == exp['s0030']['arcs']['C_SAC003'][660], f's0030 {v}'
    wyt = pg.evaluate('() => D.wyt[55]')
    assert wyt == exp['s0030']['wyt'][55], 'wyt not swapped'
    pg.screenshot(path=f'{OUT}/1_s0030_detail.png')

    # -- same theme, severe climate (s0091)
    pg.click('#scenrow1 .hydbtns button[data-h="cc95"]')
    wait_sid(pg, 's0091')
    v = arcq(pg, 'C_SAC003', 660)
    assert v == exp['s0091']['arcs']['C_SAC003'][660], f's0091 {v}'
    r = pg.evaluate("() => D.res.find(r=>r.i==='S_SHSTA').s[300]")
    assert r == exp['s0091']['res']['S_SHSTA'][300], f's0091 res {r}'
    pg.screenshot(path=f'{OUT}/2_s0091_detail.png')

    # -- big picture with a scenario that has simple data
    pg.click('#simplebtn')
    pg.wait_for_timeout(1200)
    assert pg.locator('#nosimplenote').is_hidden(), 'notice shown wrongly'
    pg.screenshot(path=f'{OUT}/3_s0091_simple.png')

    # -- USBR Alt3 run: simple mode must show the notice, not stale bars
    pg.select_option('#scenrow2 select', '5.4')
    wait_sid(pg, 's0098')
    assert pg.locator('#nosimplenote').is_visible(), 'no-simple notice missing'
    assert pg.evaluate('() => SD') is None, 'SD should be null'
    pg.screenshot(path=f'{OUT}/4_s0098_simple_notice.png')

    # -- back to baseline restores embedded data exactly
    pg.click('#detailgo')
    pg.select_option('#scenrow1 select', '1.1')
    wait_sid(pg, 's0020')
    v = arcq(pg, 'C_SAC003', 660)
    assert v == v0, f'restore mismatch {v} != {v0}'
    assert pg.evaluate('() => SD === SD0'), 'SD0 not restored'
    pg.screenshot(path=f'{OUT}/5_back_to_s0020.png')

    b.close()
srv.shutdown()
if errors:
    print('PAGE ERRORS:'); [print(' ', e) for e in errors]; sys.exit(1)
print('scenario switching OK; screenshots in', OUT)
