# CalSim3 Central Valley Water Map — Project Notes

*Last updated: July 4, 2026*

## What this is

An interactive, single-file HTML map (`CalSim3_water_map.html`, ~4.9 MB) visualizing California's Central Valley water allocation system as simulated by CalSim3 (COEQWAL scenario s0020, L2020A), Oct 1921 – Sep 2021 monthly. Built for a public audience. Open in any browser; requires internet for the basemap tiles and Leaflet CDN.

## Source data

- `s0020_coeqwal_calsim_output.csv` — wide-format DSS export, 21,493 variables × 1,200 months. Header rows: a/b/c/e/f parts, type, units.
- `20221103v2_cs3_cvhydroregion.gpkg` — CalSim3 arcs (2,118), nodes (1,400), 68 selected reservoirs, plus context layers. EPSG:3310.
- `Shapefiles/DemandUnits.shp` — 236 demand-unit polygons, `DU_ID` field, Teale Albers.
- `Calsim3GIS.qgs` — original QGIS project; references external layers not present (pointer file only, not used).

## Build pipeline

Two scripts in `build/` regenerate the map from scratch:

1. `python3 build/rebuild_data.py` — selects major features from the geopackage, simplifies geometry (RDP 50 m arcs / 75 m polygons), reprojects to WGS84, extracts all time series from the CSV, writes `build/payload.json`. Requires `pyproj` and `pyshp`.
2. `python3 build/make_html.py` — injects the payload into the HTML template and writes `CalSim3_water_map.html`.

## Map features

Flow-scaled river/canal/bypass lines (434 arcs); reservoir circles with capacity rings (62); animated flow-direction particles on the aqueducts, Delta channels, and mainstems — red when flow reverses; Banks and Jones pumping plants as export-scaled triangles; demand-unit delivery choropleth (223 polygons, shaded by applied-water depth, colored ag/urban/refuge, visible at zoom ≥ 8); timeline strip with Sacramento water-year-type bands and total-storage curve; month scrubber with play/pause and speed control; four guided story buttons (1976–77 drought, 1997 flood, Delta reversal, 2012–17 drought-to-deluge); click any feature for a 100-year chart with monthly climatology; dual-unit tooltips (cfs + TAF/month).

## Technical facts worth remembering

- **Join keys.** Arcs join CSV via `Arc_ID` — case-insensitively (`C_SJR053b` → `C_SJR053B`; case-blind matching recovers 12 arcs). Reservoirs join via `S_` + `CalSim_ID` (62/68 match). Demand units join delivery columns via exact `DU_ID` token at the end of `D_*` DIVERSION variable names (175/235 DUs; the ~60 without matches are groundwater-supplied NU/NA units, shown dashed).
- **Direction convention verified.** All 993 checkable CH arc geometries are digitized From_Node → To_Node; negative flows mean reverse flow. OMR arcs are negative ~97% of months; lower SJR (`C_SJR006/009/013`) ~33%.
- **Water year type.** `WYT_SAC_` varies within a year (forecast updates); the September value is the final 40-30-30 classification and matched all 8 verification years.
- **Exports.** Banks = `D_OMR027_CAA000` (peak 9,107 cfs), Jones = `D_OMR028_DMC000` (peak 4,600 cfs = capacity). Located at first vertices of `C_CAA000` / `C_DMC003`.
- **Unit conversion.** cfs → AF/month = cfs × 1.98347 × days-in-month.
- **Contra Costa Canal** channel arcs (`C_CCC004/007`) are absent from this CSV export — only the diversion `D_RSL004_CCC004` exists.
- **Tuning knobs.** `DEPTH_REF = 0.6` ft/month (delivery shading saturation); particle speed `0.15 + 1.0*sqrt(q/QP)` px/frame; playback 1500/800/400 ms per month; flow-width reference = 98th percentile (`qref`); particle cap 2,500.

## Remaining improvements (discussed, not yet built)

1. **Second scenario comparison** — A/B toggle or difference view ("what if"), which is the point of COEQWAL. **Deferred (July 2026):** scenario data will move from large CSV exports to a database; hold until that connectivity exists rather than building CSV-merge plumbing that gets replaced. Design discussion so far favors phased approach: A/B toggle + dual-scenario click-charts first, difference view later.
2. **Environmental context** — minimum-instream-flow requirement variables (`FLOW-MIN-INSTREAM` type) vs actual flow on key reaches; relevant to the salmon/ecological audience.
3. **About panel** — data source, scenario ID, "simulated, not observed" caveat, plain-language how-to-read guide. Important for public credibility before release.
4. **Basemap licensing + mobile pass** — verify CARTO tile usage terms or self-host tiles for a public site; controls need a responsive layout for phones.
5. **Reservoir labels** at higher zoom levels for the major reservoirs.
6. **Filter or cluster the smallest reservoirs** (many of the 62 are tiny high-Sierra pools that clutter at statewide zoom).
7. **Video export** — render frames to MP4 for social media (or a Blender import pipeline for a 3D rendered version, given the Blender 5 workflow).
8. **Groundwater pumping** (`GP_*` variables) as a complement to the surface-delivery choropleth.
9. **Delta Cross Channel / additional Delta channels** if a future CSV export includes them.

## Verification history

Every layer was spot-checked against the raw CSV after each build (values, dates, signs, unit conversions) — all matched. JS syntax checked with `node --check` after each edit.
