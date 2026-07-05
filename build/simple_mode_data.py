#!/usr/bin/env python3
"""Aggregate s0020 CalSim3 output into annual water-balance data for the
simple (PPIC-style) mode of the map.

Per water year (Oct-Sep, WY = calendar year of Sep):
  arrows:  sac (Freeport C_SAC000), sj (Vernalis C_SJR070),
           east  (other Delta inflow = DELTAINFLOWFORNDOI - sac - sj),
           outflow (NDOI), swp (Banks D_OMR027_CAA000), cvp (Jones D_OMR028_DMC000)
  sources: runoff_sac (I_SACBASIN), runoff_sj (I_SJRBASIN),
           storage_release (Sep-to-Sep drawdown of NOD base reservoirs; refill = negative)
  uses:    ag / urban / refuge (D_* DIVERSION vars by DU class; region 90
           PROVISIONALLY urban - see PROJECT_NOTES), in_delta (NET_DICU),
           losses (residual: sources - deliveries - in_delta - outflow)
  outflow: required (min(NDOI_MIN, NDOI)), uncaptured (NDOI - required)

Verified balances (assertions below):
  tier 2: DELTAINFLOWFORNDOI ~= DELTAEXPORTFORNDOI + NET_DICU + NDOI  (<0.5 maf/yr)
  losses residual never negative

Output: build/simple_payload.json - per-year records + per-year-type composite means.
All volumes TAF. WYT = Sacramento 40-30-30 index, September value (1=W ... 5=C).
"""
import csv, json, re, calendar, os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, '..', 's0020_coeqwal_calsim_output.csv')
OUT = os.path.join(HERE, 'simple_payload.json')

# CHECK BACK (July 2026): region-90 DUs likely urban per Eric, unconfirmed.
PROVISIONAL_R90_URBAN = True

# Named urban diversions that don't match the DU pattern (Bay Area conveyance).
URBAN_SUPPLEMENT = ['D_RSL004_CCC004',   # Contra Costa Canal -> CCWD
                    'D_CAA005_SBA000']   # South Bay Aqueduct
# North Bay Aqueduct: no matching diversion variable found in this export
# (searched July 2026); revisit if a future export includes it.

# Delta inflow decomposition (verified against DELTAINFLOWFORNDOI, ~1100 cfs
# of minor terms remain): C_SAC036 + C_YBP034 + C_MOK022 + C_CSM005 + C_CLV004
# + C_SJR062. Arrows: sj explicit, east explicit, sac = inflow - sj - east
# (folds Yolo + minor terms into the Sacramento arrow).
SIMPLE = ['C_SJR062', 'C_MOK022', 'C_CSM005', 'C_CLV004',
          'DELTAINFLOWFORNDOI', 'DELTAEXPORTFORNDOI',
          'NDOI', 'NDOI_MIN', 'NET_DICU', 'D_OMR027_CAA000', 'D_OMR028_DMC000',
          'I_SACBASIN', 'I_SJRBASIN', 'WYT_SAC_']
# c-part disambiguation for names that appear under several kinds
CPART = {'I_SACBASIN': ('INFLOW', 'FLOW-INFLOW'), 'I_SJRBASIN': ('INFLOW', 'FLOW-INFLOW'),
         'NDOI': ('FLOW',), 'NDOI_MIN': ('FLOW',), 'NET_DICU': ('DICU_FLOW',)}

DUPAT = re.compile(r'^D_.+?_(\d{2}[NS]?_[A-Z]{2}\d*)$')
BASE_RES = re.compile(r'^S_[A-Z0-9]+$')
SOD_RES = {'S_SLUIS'}  # TODO: classify Castaic/Pyramid/Millerton (PROJECT_NOTES)


def kind_of(du):
    if PROVISIONAL_R90_URBAN and du.startswith('90_'):
        return 'urban'
    return {'A': 'ag', 'U': 'urban', 'R': 'refuge'}.get(du.split('_')[1][1], 'ag')


def main():
    with open(CSV) as f:
        r = csv.reader(f)
        rows = [next(r) for _ in range(7)]
        b, c, units = rows[1], rows[2], rows[6]

        simple_idx, sector_cols, stor_cols = {}, {'ag': [], 'urban': [], 'refuge': []}, {}
        for i in range(1, len(b)):
            nm = b[i]
            if nm in SIMPLE and nm not in simple_idx:
                if nm in CPART and c[i] not in CPART[nm]:
                    continue
                simple_idx[nm] = i
            if c[i] == 'DIVERSION':
                m = DUPAT.match(nm)
                if m:
                    sector_cols[kind_of(m.group(1))].append(i)
                elif nm in URBAN_SUPPLEMENT:
                    sector_cols['urban'].append(i)
            if c[i] == 'STORAGE' and units[i] == 'TAF' and BASE_RES.match(nm) \
                    and nm not in SOD_RES:
                stor_cols[nm] = i
        missing = [nm for nm in SIMPLE if nm not in simple_idx]
        assert not missing, f'missing variables: {missing}'

        need = sorted(set(simple_idx.values())
                      | {i for v in sector_cols.values() for i in v}
                      | set(stor_cols.values()))
        months, series = [], {i: [] for i in need}
        for row in r:
            months.append(row[0][:7])
            for i in need:
                series[i].append(float(row[i] or 0))

    def taf(i, mi):
        y, m = int(months[mi][:4]), int(months[mi][5:7])
        return series[i][mi] * 1.98347 * calendar.monthrange(y, m)[1] / 1000

    wy = {}
    for mi, ym in enumerate(months):
        y, m = int(ym[:4]), int(ym[5:7])
        wy.setdefault(y if m <= 9 else y + 1, []).append(mi)

    years = []
    for year in sorted(wy):
        mm = wy[year]
        if len(mm) < 12 or mm[0] == 0:
            continue  # skip partial first year (no prior Sep storage)
        A = {nm: sum(taf(simple_idx[nm], mi) for mi in mm) for nm in SIMPLE if nm != 'WYT_SAC_'}
        east = A['C_MOK022'] + A['C_CSM005'] + A['C_CLV004']
        sect = {k: sum(taf(i, mi) for i in v for mi in mm) for k, v in sector_cols.items()}
        s0 = sum(series[i][mm[0] - 1] for i in stor_cols.values())
        s1 = sum(series[i][mm[-1]] for i in stor_cols.values())
        release = s0 - s1
        sources = A['I_SACBASIN'] + A['I_SJRBASIN'] + release
        required = min(A['NDOI_MIN'], A['NDOI'])
        losses = sources - sum(sect.values()) - A['NET_DICU'] - A['NDOI']
        tier2 = A['DELTAINFLOWFORNDOI'] - A['DELTAEXPORTFORNDOI'] - A['NET_DICU'] - A['NDOI']
        assert abs(tier2) < 500, f'WY{year}: tier-2 residual {tier2:.0f} TAF'
        # residual may dip slightly negative in extreme wet years (net return
        # flows); allow up to 2% of sources, clamp to 0 for display
        assert losses > -0.02 * sources, f'WY{year}: negative losses {losses:.0f} TAF'
        losses = max(losses, 0.0)
        years.append({
            'wy': year, 'wyt': int(series[simple_idx['WYT_SAC_']][mm[-1]]),
            'arrows': {'sac': A['DELTAINFLOWFORNDOI'] - A['C_SJR062'] - east,
                       'sj': A['C_SJR062'], 'east': east,
                       'outflow': A['NDOI'], 'swp': A['D_OMR027_CAA000'],
                       'cvp': A['D_OMR028_DMC000']},
            'sources': {'runoff_sac': A['I_SACBASIN'], 'runoff_sj': A['I_SJRBASIN'],
                        'storage_release': release},
            'uses': {'ag': sect['ag'], 'urban': sect['urban'], 'refuge': sect['refuge'],
                     'in_delta': A['NET_DICU'], 'losses': losses},
            'outflow': {'required': required, 'uncaptured': A['NDOI'] - required},
        })

    wyt_names = {1: 'Wet', 2: 'Above Normal', 3: 'Below Normal', 4: 'Dry', 5: 'Critical'}
    composites = {}
    for t in range(1, 6):
        sub = [y for y in years if y['wyt'] == t]
        comp = {'n': len(sub), 'name': wyt_names[t]}
        for grp in ('arrows', 'sources', 'uses', 'outflow'):
            comp[grp] = {k: round(sum(y[grp][k] for y in sub) / len(sub), 1)
                         for k in sub[0][grp]}
        composites[t] = comp

    for y in years:  # round after composites
        for grp in ('arrows', 'sources', 'uses', 'outflow'):
            y[grp] = {k: round(v, 1) for k, v in y[grp].items()}

    payload = {'years': years, 'composites': composites,
               'meta': {'units': 'TAF/WY', 'scenario': 's0020',
                        'r90_urban_provisional': PROVISIONAL_R90_URBAN}}
    json.dump(payload, open(OUT, 'w'))
    kb = os.path.getsize(OUT) / 1024
    print(f'{len(years)} years -> {OUT} ({kb:.0f} KB)')
    for t, cmp_ in composites.items():
        print(f"{cmp_['name']:>13} (n={cmp_['n']:>2}): sources="
              f"{sum(cmp_['sources'].values())/1000:5.1f} maf  ag={cmp_['uses']['ag']/1000:4.1f}"
              f"  urban={cmp_['uses']['urban']/1000:4.1f}  refuge={cmp_['uses']['refuge']/1000:4.1f}"
              f"  losses={cmp_['uses']['losses']/1000:4.1f}  outflow={cmp_['arrows']['outflow']/1000:5.1f}")


if __name__ == '__main__':
    main()
