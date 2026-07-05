#!/usr/bin/env python3
"""Static SVG mockup of the simple-mode brushed arrows (PPIC style).
Two panels: average Wet vs average Critical year, arrow width proportional to volume.
Reads build/simple_payload.json; writes build/simple_arrows_mockup.svg.
Arrow centerlines are hand-authored cubic beziers in lon/lat."""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
payload = json.load(open(os.path.join(HERE, 'simple_payload.json')))
outline = json.load(open(os.path.join(HERE, 'ca_outline.json')))

# --- projection: equirectangular, per-panel offset
LON0, LON1, LAT0, LAT1 = -125.2, -113.8, 32.2, 42.3
KX = math.cos(math.radians(37.0))
PW, PH = 460, 560          # panel size
PAD_TOP = 70


def proj(lon, lat, ox):
    x = (lon - LON0) / (LON1 - LON0) * KX * PW / KX
    y = (LAT1 - lat) / (LAT1 - LAT0) * PH
    return ox + x * 0.98, PAD_TOP + y


# --- arrow centerlines: cubic bezier control points (lon,lat)
ARROWS = {
    'sac':     {'pts': [(-122.25, 40.45), (-122.05, 39.6), (-121.75, 39.05), (-121.8, 38.4)],
                'color': '#4a90c4', 'label_t': 0.45, 'dlab': (-58, 0)},
    'east':    {'pts': [(-120.65, 38.7), (-121.0, 38.5), (-121.25, 38.4), (-121.55, 38.25)],
                'color': '#4a90c4', 'label_t': 0.1, 'dlab': (34, -12)},
    'sj':      {'pts': [(-119.8, 36.9), (-120.5, 37.05), (-121.05, 37.35), (-121.55, 37.9)],
                'color': '#4a90c4', 'label_t': 0.02, 'dlab': (48, 10)},
    'outflow': {'pts': [(-122.05, 38.05), (-122.3, 38.02), (-122.55, 37.88), (-123.1, 37.5)],
                'color': '#2b6ca3', 'label_t': 0.95, 'dlab': (-14, 34)},
    'swp':     {'pts': [(-121.68, 37.68), (-121.0, 36.5), (-119.95, 35.55), (-118.95, 34.85)],
                'color': '#d97e2a', 'label_t': 0.72, 'dlab': (42, 4)},
    'cvp':     {'pts': [(-121.55, 37.6), (-121.35, 37.2), (-121.1, 36.95), (-120.7, 36.7)],
                'color': '#a85d1c', 'label_t': 1.0, 'dlab': (-26, 30)},
}
NAMES = {'sac': 'Sacramento', 'sj': 'San Joaquin', 'east': 'Eastside',
         'outflow': 'Delta outflow', 'swp': 'SWP exports', 'cvp': 'CVP exports'}

PX_PER_MAF = 1.5           # arrow width scale
MIN_W = 2.2


def bez(p, t):
    u = 1 - t
    return tuple(u**3*p[0][i] + 3*u*u*t*p[1][i] + 3*u*t*t*p[2][i] + t**3*p[3][i]
                 for i in (0, 1))


def arrow_polygon(ctrl_xy, w):
    """Constant-width wedge with triangular head along a cubic bezier (pixel ctrl pts)."""
    n = 48
    pts = [bez(ctrl_xy, i / n) for i in range(n + 1)]
    head_len = min(max(w * 1.15, 10), 24)
    # trim tail of centerline by head_len for the head base
    total = sum(math.dist(pts[i], pts[i+1]) for i in range(n))
    acc, cut = 0, n
    for i in range(n, 0, -1):
        acc += math.dist(pts[i-1], pts[i])
        if acc >= head_len:
            cut = i - 1
            break
    body = pts[:cut+1]
    tip = pts[-1]

    def normal(i, arr):
        a = arr[max(i-1, 0)]
        b = arr[min(i+1, len(arr)-1)]
        dx, dy = b[0]-a[0], b[1]-a[1]
        L = math.hypot(dx, dy) or 1
        return -dy/L, dx/L
    left, right = [], []
    for i, p in enumerate(body):
        nx, ny = normal(i, body)
        left.append((p[0]+nx*w/2, p[1]+ny*w/2))
        right.append((p[0]-nx*w/2, p[1]-ny*w/2))
    nx, ny = normal(len(body)-1, body)
    hb = body[-1]
    hw = min(w * 0.95, 14)  # head half-extension beyond body edge, capped
    poly = left + [(hb[0]+nx*(w/2+hw), hb[1]+ny*(w/2+hw)), tip,
                   (hb[0]-nx*(w/2+hw), hb[1]-ny*(w/2+hw))] + right[::-1]
    return poly


def fmt_pts(poly):
    return ' '.join(f'{x:.1f},{y:.1f}' for x, y in poly)


def panel(comp, ox, title):
    s = []
    s.append(f'<text x="{ox + PW*0.42}" y="46" class="ptitle">{title}</text>')
    ring = ' '.join(f'{x:.1f},{y:.1f}' for x, y in (proj(lo, la, ox) for lo, la in outline))
    s.append(f'<polygon points="{ring}" fill="#ececec" stroke="#b5b5b5" stroke-width="1"/>')
    a = comp['arrows']
    for key, spec in ARROWS.items():
        maf = a[key] / 1000
        w = max(maf * PX_PER_MAF, MIN_W)
        ctrl = [proj(lo, la, ox) for lo, la in spec['pts']]
        poly = arrow_polygon(ctrl, w)
        s.append(f'<polygon points="{fmt_pts(poly)}" fill="{spec["color"]}" '
                 f'fill-opacity="0.82"/>')
        lx, ly = bez(ctrl, spec['label_t'])
        dx, dy = spec['dlab']
        s.append(f'<text x="{lx+dx:.0f}" y="{ly+dy:.0f}" class="alab">{NAMES[key]}</text>')
        s.append(f'<text x="{lx+dx:.0f}" y="{ly+dy+13:.0f}" class="aval">{maf:.1f} maf</text>')
    return '\n'.join(s)


W = 2 * PW + 60
H = PH + PAD_TOP + 90
wet, crit = payload['composites']['1'], payload['composites']['5']
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
       f'font-family="Helvetica,Arial,sans-serif">',
       '<style>.ptitle{font-size:19px;fill:#555;text-anchor:middle}'
       '.alab{font-size:12.5px;fill:#333;font-weight:600;text-anchor:middle}'
       '.aval{font-size:12px;fill:#666;text-anchor:middle}'
       '.t{font-size:23px;fill:#444}.leg{font-size:12px;fill:#555}</style>',
       f'<rect width="{W}" height="{H}" fill="white"/>',
       '<text x="24" y="30" class="t">Where the water goes — average year by type '
       '(CalSim3, s0020)</text>',
       panel(wet, 20, f"Wet year (average of {wet['n']})"),
       panel(crit, PW + 40, f"Critical year (average of {crit['n']})")]
# scale legend, bottom left
for i, maf in enumerate((5, 25)):
    w = maf * PX_PER_MAF
    x = 50 + i * 60
    y0 = H - 30
    svg.append(f'<polygon points="{fmt_pts(arrow_polygon([(x, y0), (x, y0-20), (x, y0-40), (x, y0-58)], w))}" fill="#4a90c4" fill-opacity="0.82"/>')
    svg.append(f'<text x="{x}" y="{H-10}" class="leg" text-anchor="middle">{maf} maf</text>')
svg.append('</svg>')
out = os.path.join(HERE, 'simple_arrows_mockup.svg')
open(out, 'w').write('\n'.join(svg))
print(out)
