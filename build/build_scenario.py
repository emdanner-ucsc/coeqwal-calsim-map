#!/usr/bin/env python3
"""Extract one scenario's time series for the map -> scenarios/<sid>.json

Usage: python3 build/build_scenario.py <csv_path> [outdir]

Feature set (which arcs/reservoirs/DUs appear) is FROZEN from the base
payload (build/payload.json, built from s0020 by rebuild_data.py); this
script only extracts series for those features from another scenario's
CSV, joining by variable NAME (case-insensitive), never by column index
(column layouts differ between scenario exports: 17k-24k columns).

Output (~5 MB raw, ~1-2 MB gzipped over the wire):
  {"sid": "s0025",
   "wyt":   [100 ints],                     # Sac 40-30-30, September value
   "arcs":  {"C_SAC000": [1200 cfs|null], ...},   # majors + minors
   "res":   {"S_SHSTA": [1200 TAF|null], ...},
   "pumps": {"D_OMR027_CAA000": [...], ...},
   "dus":   {"01_PA1": [1200 TAF/month], ...},
   "simple": {...simple_payload...} | null}      # null if I_*BASIN absent
                                                  # (USBR Alt3 runs, family 5.x)

Rounding matches rebuild_data.py: arcs/pumps int cfs, res 0.1 TAF, dus 0.01 TAF.
qref / capacity rings / particle scaling stay frozen from the base payload so
line widths and circle sizes are visually comparable across scenarios.
"""
import csv, json, re, os, sys, calendar
from collections import defaultdict

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DUPAT = re.compile(r'^D_.+?_(\d{2}[NS]?_[A-Z]{2}\d*)$')
BASE_RES = re.compile(r'^S_[A-Z0-9]+$')
SOD_RES = {'S_SLUIS'}
PROVISIONAL_R90_URBAN = True
URBAN_SUPPLEMENT = ['D_RSL004_CCC004', 'D_CAA005_SBA000']
SIMPLE_VARS = ['C_SJR062', 'C_MOK022', 'C_CSM005', 'C_CLV004',
               'DELTAINFLOWFORNDOI', 'DELTAEXPORTFORNDOI',
               'NDOI', 'NDOI_MIN', 'NET_DICU', 'D_OMR027_CAA000',
               'D_OMR028_DMC000', 'I_SACBASIN', 'I_SJRBASIN', 'WYT_SAC_']
SIMPLE_CPART = {'I_SACBASIN': ('INFLOW', 'FLOW-INFLOW'),
                'I_SJRBASIN': ('INFLOW', 'FLOW-INFLOW'),
                'NDOI': ('FLOW',), 'NDOI_MIN': ('FLOW',),
                'NET_DICU': ('DICU_FLOW',)}


def kind_of(du):
    if PROVISIONAL_R90_URBAN and du.startswith('90_'):
        return 'urban'
    return {'A': 'ag', 'U': 'urban', 'R': 'refuge'}.get(du.split('_')[1][1], 'ag')


def main(csv_path, outdir):
    sid = os.path.basename(csv_path).split('_')[0]
    base = json.load(open(os.path.join(HERE, 'payload.json')))
    arc_ids = [a['i'] for a in base['arcs']] + [a['i'] for a in base['marcs']]
    res_ids = [r['i'] for r in base['res']]
    pump_ids = [p['i'] for p in base['pumps']]
    du_ids = [d['i'] for d in base['dus'] if 'd' in d]   # delivery DUs only

    # ---- header: name -> column, honoring c-part disambiguation
    with open(csv_path) as f:
        r = csv.reader(f)
        rows = [next(r) for _ in range(7)]
    b, c, units = rows[1], rows[2], rows[6]

    chan, stor, div, first, simple_idx = {}, {}, {}, {}, {}
    du_cols, supp_cols = defaultdict(list), []
    for i in range(1, len(b)):
        nm = b[i]; u = nm.upper()
        if u not in first:
            first[u] = i
        if c[i] == 'CHANNEL' and u not in chan:
            chan[u] = i
        elif c[i] == 'STORAGE' and units[i] == 'TAF' and u not in stor:
            stor[u] = i
        elif c[i] == 'DIVERSION':
            if u not in div:
                div[u] = i
            m = DUPAT.match(nm)
            if m:
                du_cols[m.group(1)].append(i)
            elif nm in URBAN_SUPPLEMENT:
                supp_cols.append(i)
        if nm in SIMPLE_VARS and nm not in simple_idx:
            if nm in SIMPLE_CPART and c[i] not in SIMPLE_CPART[nm]:
                continue
            simple_idx[nm] = i

    def col(nm, pref):
        return pref.get(nm.upper(), first.get(nm.upper()))

    arc_col = {i_: col(i_, chan) for i_ in arc_ids}
    res_col = {i_: col(i_, stor) for i_ in res_ids}
    pump_col = {i_: col(i_, div) for i_ in pump_ids}
    wyt_col = first.get('WYT_SAC_')
    assert wyt_col, 'WYT_SAC_ missing'
    for kind, m in (('arc', arc_col), ('res', res_col), ('pump', pump_col)):
        for k, v in m.items():
            if v is None:
                print(f'  WARN {sid}: no {kind} column for {k}')

    simple_missing = [v for v in SIMPLE_VARS if v not in simple_idx]
    do_simple = not simple_missing
    if simple_missing:
        print(f'  {sid}: simple mode OFF (missing {simple_missing})')

    # storage columns for simple-mode release calc (base-name S_*, no SOD)
    stor_simple = {nm: i for nm, i in ((b[i], i) for i in stor.values())
                   if BASE_RES.match(nm) and nm not in SOD_RES} if do_simple else {}

    need = sorted({v for v in arc_col.values() if v is not None}
                  | {v for v in res_col.values() if v is not None}
                  | {v for v in pump_col.values() if v is not None}
                  | {i for cols in du_cols.values() for i in cols}
                  | set(supp_cols)
                  | set(simple_idx.values()) | set(stor_simple.values())
                  | {wyt_col, 0})

    df = pd.read_csv(csv_path, skiprows=7, header=None, usecols=need,
                     na_values=[''], low_memory=False)
    months = [str(v)[:7] for v in df[0]]
    assert months == base['months'], f'{sid}: month axis differs from base'
    S = {i: df[i].to_numpy(dtype=float) for i in need if i != 0}

    def ser(i, nd):
        # nd=0 replicates rebuild_data.py's double round: round(round(v,1))
        if i is None:
            return [None] * len(months)
        return [None if v != v else
                (round(float(v), nd) if nd else round(round(float(v), 1)))
                for v in S[i]]

    out = {'sid': sid,
           'wyt': [int(S[wyt_col][wy * 12 + 11]) for wy in range(len(months) // 12)],
           'arcs': {k: ser(v, 0) for k, v in arc_col.items()},
           'res': {k: ser(v, 1) for k, v in res_col.items()},
           'pumps': {k: ser(v, 0) for k, v in pump_col.items()}}

    DAYS = [calendar.monthrange(int(m[:4]), int(m[5:7]))[1] for m in months]
    dus = {}
    for du in du_ids:
        cols = du_cols.get(du, [])
        if not cols:
            print(f'  WARN {sid}: no delivery columns for DU {du}, zero-filled')
            dus[du] = [0.0] * len(months)
            continue
        tot = sum(S[i] for i in cols)
        dus[du] = [round((0 if v != v else v) * 1.98347 * DAYS[mi] / 1000, 2)
                   for mi, v in enumerate(tot)]
    out['dus'] = dus

    out['simple'] = simple_payload(sid, months, S, simple_idx, du_cols,
                                   supp_cols, stor_simple, DAYS) if do_simple else None

    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, sid + '.json')
    json.dump(out, open(path, 'w'), separators=(',', ':'))
    print(f'  {sid}: {os.path.getsize(path)/1e6:.2f} MB'
          f'{"" if do_simple else " (no simple mode)"}')


def simple_payload(sid, months, S, idx, du_cols, supp_cols, stor_cols, DAYS):
    """Port of simple_mode_data.py, computed from the already-read columns."""
    sector_cols = {'ag': [], 'urban': [], 'refuge': []}
    for du, cols in du_cols.items():
        sector_cols[kind_of(du)].extend(c for c in cols if c in S)
    sector_cols['urban'].extend(supp_cols)  # CCC->CCWD, SBA (Bay Area conveyance)

    def taf(i, mi):
        return S[i][mi] * 1.98347 * DAYS[mi] / 1000

    wy = {}
    for mi, ym in enumerate(months):
        y, m = int(ym[:4]), int(ym[5:7])
        wy.setdefault(y if m <= 9 else y + 1, []).append(mi)

    years = []
    for year in sorted(wy):
        mm = wy[year]
        if len(mm) < 12 or mm[0] == 0:
            continue
        A = {nm: sum(taf(idx[nm], mi) for mi in mm)
             for nm in idx if nm != 'WYT_SAC_'}
        east = A['C_MOK022'] + A['C_CSM005'] + A['C_CLV004']
        sect = {k: sum(taf(i, mi) for i in v for mi in mm)
                for k, v in sector_cols.items()}
        s0 = sum(S[i][mm[0] - 1] for i in stor_cols.values())
        s1 = sum(S[i][mm[-1]] for i in stor_cols.values())
        release = s0 - s1
        sources = A['I_SACBASIN'] + A['I_SJRBASIN'] + release
        required = min(A['NDOI_MIN'], A['NDOI'])
        losses = sources - sum(sect.values()) - A['NET_DICU'] - A['NDOI']
        tier2 = (A['DELTAINFLOWFORNDOI'] - A['DELTAEXPORTFORNDOI']
                 - A['NET_DICU'] - A['NDOI'])
        if abs(tier2) >= 500:
            print(f'  WARN {sid} WY{year}: tier-2 residual {tier2:.0f} TAF')
        # The residual is NEGATIVE for some scenario families (notably 3.1,
        # remove-min-flows: most years) — i.e. unaccounted net inflow. Show it
        # honestly on the sources bar instead of clamping it away (July 2026).
        other = max(-losses, 0.0)
        losses = max(losses, 0.0)
        years.append({
            'wy': year, 'wyt': int(S[idx['WYT_SAC_']][mm[-1]]),
            'arrows': {'sac': A['DELTAINFLOWFORNDOI'] - A['C_SJR062'] - east,
                       'sj': A['C_SJR062'], 'east': east,
                       'outflow': A['NDOI'], 'swp': A['D_OMR027_CAA000'],
                       'cvp': A['D_OMR028_DMC000']},
            'sources': {'runoff_sac': A['I_SACBASIN'],
                        'runoff_sj': A['I_SJRBASIN'],
                        'storage_release': release, 'other': other},
            'uses': {'ag': sect['ag'], 'urban': sect['urban'],
                     'refuge': sect['refuge'], 'in_delta': A['NET_DICU'],
                     'losses': losses},
            'outflow': {'required': required,
                        'uncaptured': A['NDOI'] - required},
        })

    composites = {}
    wyt_names = {1: 'Wet', 2: 'Above Normal', 3: 'Below Normal',
                 4: 'Dry', 5: 'Critical'}
    for t in range(1, 6):
        sub = [y for y in years if y['wyt'] == t]
        if not sub:
            continue
        comp = {'n': len(sub), 'name': wyt_names[t]}
        for grp in ('arrows', 'sources', 'uses', 'outflow'):
            comp[grp] = {k: round(sum(y[grp][k] for y in sub) / len(sub), 1)
                         for k in sub[0][grp]}
        composites[t] = comp
    for y in years:
        for grp in ('arrows', 'sources', 'uses', 'outflow'):
            y[grp] = {k: round(v, 1) for k, v in y[grp].items()}
    return {'years': years, 'composites': composites,
            'meta': {'units': 'TAF/WY', 'scenario': sid,
                     'r90_urban_provisional': PROVISIONAL_R90_URBAN}}


if __name__ == '__main__':
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'scenarios')
    main(sys.argv[1], outdir)
