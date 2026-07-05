"""Phone-viewport screenshot harness (390x844) for CalSim3_water_map.html.

Companion to build/screenshot.py (same vendor/route trick — see that file
and build/sandbox_setup.sh). Covers the mobile layouts: About, simple-mode
bottom sheet (closed + Breakdown open), and detailed-mode compact header.

Usage: python3 build/screenshot_mobile.py [outdir]
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'build' / 'shots_mobile'
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
    pg = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                    is_mobile=True, has_touch=True)
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.route('**/*', route)
    pg.goto((ROOT / 'CalSim3_water_map.html').as_uri())
    pg.wait_for_timeout(5000)
    pg.screenshot(path=str(OUT / 'm1_about.png'))
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / 'm2_simple_sheet.png'))
    pg.click('#skeytoggle')
    pg.wait_for_timeout(800)
    pg.screenshot(path=str(OUT / 'm3_simple_breakdown.png'))
    pg.click('#skeytoggle')
    pg.wait_for_timeout(400)
    pg.evaluate("setMode(false)")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / 'm4_detail.png'))
    pg.evaluate("map.setView([37.95,-121.5],10); render(660);")
    pg.wait_for_timeout(2500)
    pg.screenshot(path=str(OUT / 'm5_detail_delta.png'))
    b.close()

print('screenshots in', OUT)
if errors:
    print('PAGE ERRORS:'); [print(' ', e[:200]) for e in errors]
    sys.exit(1)
print('no page errors')
