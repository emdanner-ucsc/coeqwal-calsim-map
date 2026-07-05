"""Headless screenshot harness for CalSim3_water_map.html.

Renders the map in headless Chromium and writes PNGs for visual
verification. Works in offline/proxied sandboxes: CDN requests for
Leaflet are served from build/vendor/, basemap tile requests are
aborted (background stays gray; all data layers still render).

Setup (once per environment): see build/sandbox_setup.sh
Usage: python3 build/screenshot.py [outdir]
"""
import os, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'build' / 'shots'
OUT.mkdir(parents=True, exist_ok=True)
VENDOR = ROOT / 'build' / 'vendor'

from playwright.sync_api import sync_playwright

def route(r):
    url = r.request.url
    if 'leaflet.min.js' in url or url.endswith('leaflet.js'):
        r.fulfill(path=str(VENDOR / 'leaflet.js'), content_type='application/javascript')
    elif 'leaflet.min.css' in url or url.endswith('leaflet.css'):
        r.fulfill(path=str(VENDOR / 'leaflet.css'), content_type='text/css')
    elif 'cartocdn' in url or 'openstreetmap' in url:
        r.abort()
    else:
        r.continue_()

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1400, 'height': 900})
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.route('**/*', route)
    pg.goto((ROOT / 'CalSim3_water_map.html').as_uri())
    pg.wait_for_timeout(5000)
    pg.screenshot(path=str(OUT / '1_about_panel.png'))
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / '2_simple_all.png'))          # lands in simple mode
    pg.evaluate("document.querySelectorAll('#wytbtns button')[5].click()")  # Critical
    pg.wait_for_timeout(800)
    pg.screenshot(path=str(OUT / '3_simple_critical.png'))
    pg.evaluate("setMode(false)")                               # detailed mode
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / '4_statewide.png'))
    # Delta close-up, mid-drought month for variety
    pg.evaluate("map.setView([37.95,-121.5],10); render(660);")
    pg.wait_for_timeout(2500)
    pg.screenshot(path=str(OUT / '5_delta.png'))
    # back to simple, confirm round-trip
    pg.evaluate("setMode(true)")
    pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / '6_simple_return.png'))
    b.close()

print('screenshots in', OUT)
if errors:
    print('PAGE ERRORS:'); [print(' ', e[:200]) for e in errors]
    sys.exit(1)
print('no page errors')
