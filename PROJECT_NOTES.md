# CalSim3 Central Valley Water Map — Project Notes

*Last updated: July 8, 2026 (session close) — shipped: **multi-scenario support** (43 scenarios, theme × hydrology picker in both modes, lazy fetch, s0020 still embedded). Negative-residual issue RESOLVED via signed split: negative years now surface as an "Other inflows (net)" segment on the sources bar (Eric's call, option 1); bars balance exactly for all 43. All three headless harnesses pass. Still open: CC50/CC95 baseline CSVs (s0047, s0056) from team; ask team what physically closes the balance in the 3.1 no-min-flow runs; CARTO licensing; region-90 DU confirmation; real-phone check.*

## What this is

An interactive, single-file HTML map (`CalSim3_water_map.html`, ~4.9 MB) visualizing California's Central Valley water allocation system as simulated by CalSim3 (COEQWAL scenario s0020, L2020A), Oct 1921 – Sep 2021 monthly. Built for a public audience. Open in any browser; requires internet for the basemap tiles and Leaflet CDN.

## Repository

Public GitHub repo: https://github.com/emdanner-ucsc/coeqwal-calsim-map (personal account; commits as emdanner@ucsc.edu, set in repo-local git config). Committed: HTML map, `build/` scripts, `Shapefiles/`, README, these notes. Gitignored: the two ~270 MB source files and `build/*.json` intermediates (regeneration steps in README). GitHub Pages not yet enabled — flip on under Settings → Pages when ready to publish (consider adding the about panel first).

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

## Simple mode — PPIC-style overview (BUILT July 5, 2026)

Implemented as a mode of the existing map: lands in simple mode (URL hash `#detail` skips it); locked statewide camera (`fitBounds`, interactions disabled, detailed panes hidden via pane `display`); six hand-authored bezier arrows in an SVG overlay (`S_ARROWS` in the template — widths scale from px-per-degree so any viewport works); year-type buttons (All + 5 WYT composites) + single-year dropdown; sources/uses/outflow stacked bars with sector colors matching the detailed legend; "Explore the detailed map →" ↔ "← Big picture" round-trip. Data: `build/simple_mode_data.py` → `build/simple_payload.json` (37 KB, injected as `__SIMPLE__`). Static mockup generator: `build/mockup_simple_arrows.py` (+ `ca_outline.json`, extracted from the gpkg `GU_StateOrTerritory` layer — already WGS84, unlike other layers which are EPSG:3310). Screenshot harness extended to 6 shots covering both modes. Remaining polish: About-panel text doesn't yet mention the two views; storage-release "Stored in reservoirs" segment appears on the uses bar in wet years (by design — flag for team review). Water balance verified from the s0020 CSV:

- **Tier 1 (upstream):** `I_SACBASIN` + `I_SJRBASIN` (basin runoff) + storage release (Sep–Sep ΔS of the 92 base-name `S_*` reservoirs, excluding `S_SLUIS`) − upstream use (residual) = `DELTAINFLOWFORNDOI`. Residual "upstream use" is always positive, mean 7.8 maf/yr, range 2.0–10.9, lower in wet years — physically plausible.
- **Tier 2 (Delta):** `DELTAINFLOWFORNDOI` = `DELTAEXPORTFORNDOI` + `NET_DICU` + `NDOI`, closes to 0.2–0.4 maf/yr (CalSim minor terms).
- **Cross-check:** WY2021 sources = 9.3 runoff + 5.8 release = 15.1 maf ≈ PPIC's published ~15 maf for 2021.
- **Arrow split:** `C_SAC000` (Freeport) + `C_SJR070` (Vernalis) = 87.5% of Delta inflow; remainder = Yolo/eastside bundle. Exports: Banks + Jones + CCC = 96.7% of `DELTAEXPORTFORNDOI`.
- **Outflow split available:** `NDOI_MIN` (required) vs `NDOI − NDOI_MIN` (uncaptured), matching PPIC's ecosystem/uncaptured distinction.
- **Refinement needed before build:** classify the 92 base reservoirs NOD vs SOD properly (Castaic/Pyramid are SWP terminal; Millerton/Friant is ambiguous — releases mostly go SOD via Friant-Kern). Beware `S_*` cycle-suffix duplicates (`_DELTA`, `_MON`, …) — use base names only.
- **Sector split (COEQWAL framing) verified July 5, 2026:** aggregating `D_*` DIVERSION vars by DU class gives ag 8.4 / urban 0.6 / refuge 0.5 maf/yr; closure residual "losses & other" = mean 4.1 maf/yr (16% of sources), never negative across 100 years (but 25–29% in critical years). **Open questions:** (1) region-90 DUs (`90_PA*`, 0.68 maf/yr — most of SoCal SWP water) classify as *ag* under the second-letter rule. **Eric's read (July 5, 2026): likely urban — treated provisionally as urban in simple-mode data; CHECK BACK with CalSim3 docs/COEQWAL team to confirm before publishing.** (2) Non-DU urban diversions (CCC→CCWD 78 TAF/yr, NBA, SBA `D_CAA005_SBA000`) currently land in losses&other; consider a curated urban supplement list.

## Multi-scenario support (July 8, 2026 — built, verification paused)

Context: the team decided the website database will NOT hold full time series for all
scenarios (CSV downloads only), so scenario data for this map is precomputed into static
per-scenario JSON — which also unblocked the long-deferred scenario comparison work.

**Built and verified this session:**
- `build/scenario_meta.json` — 20 themes × 3 hydrologies (hist/cc50/cc95), 43 runs, from
  the team's scenario-listing xlsx (Web Platform IDs, short descriptions, family groups
  1=Baselines … 7=New conveyance). Baseline gap: no CC50/CC95 baselines on hand —
  **ask team for s0047 + s0056 CSVs** so climate runs compare to their own baseline.
- `build/build_scenario.py <csv> [outdir]` — extracts one scenario → `scenarios/<sid>.json`
  (~5 MB: wyt + arcs/res/pumps/dus series keyed by ID + simple-mode payload or null).
  Joins by variable NAME (column layouts differ: 17k–24k cols). Feature set frozen from
  payload.json; qref/capacity/particle scales frozen from base for cross-scenario
  comparability. **Verified: reproduces s0020 embedded payload byte-identically**
  (needed the double-round quirk: round(round(v,1))). Uses pandas (fast: ~2.5 s/scenario).
- All 43 `scenarios/*.json` generated (~220 MB total, ~1–2 MB each gzipped over the wire).
  6 USBR Alt3 runs (5.x: s0039/41/98/99/100/101) lack I_SACBASIN/I_SJRBASIN → simple:null.
- `make_html.py`: scenario picker (theme optgroups + hydrology pill buttons) in BOTH modes;
  lazy fetch + in-memory cache (cap ~6); s0020 embedded so the single-file property holds
  for the default; file:// fallback message; `.cursid` spans update; no-simple notice for
  USBR Alt3 runs (body.nosimple); WYT buttons disable when a hydrology has no such years;
  strip rebuilt on mode switch (was zero-size if built while hidden); TSMAX has frozen
  floor at base max (comparable storage curves, never clips).
- `build/screenshot_scenarios.py` — headless harness #3: serves repo over http, drives the
  picker, asserts series/wyt swap against the JSON files, no-simple notice, exact restore
  to s0020. **All passing.** (Gotchas: must route vendor leaflet like screenshot.py; must
  Escape the about panel before clicking; use C_SAC003 — there is no C_SAC000 arc.)

**Negative-residual issue (found + RESOLVED July 8, 2026):** the tier-1 residual
"losses & other" = sources − deliveries − NET_DICU − NDOI goes NEGATIVE for the
remove-min-flows family (3.1): s0030 hist mean −0.3 maf/yr (58/99 yrs), s0071 cc50 −1.3
(75/99), s0091 cc95 −1.8 (82/99); mildly for the eflows+CVgwLU family (3.3): s0032
(16/99), s0073 (28/99). All 32 other simple-capable scenarios healthy (+1.9 to +3.5
maf/yr, ≤4 neg yrs — full audit, all 43). **Resolution (Eric's call):** store the residual
split signed — per-year `uses.losses = max(r,0)`, `sources.other = max(−r,0)` — and show
"Other inflows (net)" as a gray-blue segment on the sources bar (only drawn when
> 50 TAF). Bars now balance exactly for every scenario (verified: worst |src−use−ofl| =
0.0 TAF). Implemented identically in build_scenario.py AND simple_mode_data.py (keep in
sync!); simple_payload.json regenerated from scenarios/s0020.json (equivalent — the two
code paths were verified byte-identical). Physical interpretation still worth asking the
COEQWAL team: what closes the balance when min-flow requirements are removed?
Audit script: outputs/audit_losses.py from the July 8 session (recreate from git history
of this note if needed — computes pre-clamp residual per CSV).

**Verified July 8:** s0020.json byte-identical to embedded payload; raw-CSV spot-checks
(s0091 C_SAC003 + S_SHSTA at 1976-10, independent of pipeline); balance closure all 43;
node --check; all three harnesses (desktop 6 shots, mobile 5, scenario-switch 5 with
value assertions) pass with no page errors.

## A/B comparison view — design brief (written July 8, 2026, NOT built; discuss first)

Everything needed exists: static per-scenario JSONs, in-memory `scenCache`, frozen
qref/capacity/particle scales (visual sizes already comparable), and `applyScenario()`
which swaps series in place. Design direction from earlier discussions: **A/B toggle +
dual-scenario click-charts first, difference view later.**

Proposed minimal v1 (to discuss with Eric before building):
1. **"Compare" affordance** in the scenario picker row: adds a scenario B (same
   theme×hydrology picker UI); A/B pill buttons appear next to the month scrubber to
   flip the whole map between the two (instant — both cached). Keeps one mental model
   (the map always shows ONE scenario) and reuses applyScenario() untouched.
2. **Click-charts show both:** when B is set, drawChart() overlays B's series as a second
   line (A solid #1668a8, B dashed #e07b28?) + both values in the subtitle. This is where
   real insight lives (e.g. Shasta storage under salmon flows vs baseline). Needs
   `scenCache[bSid]` lookups keyed by feature id — data already keyed that way.
3. **Simple mode:** bars for A and B side by side (two thin tracks per bar group) —
   cheap and high-value; arrows stay A-only (two arrow sets is clutter).
4. **Timeline strip:** draw B's storage curve as a second line (dashed) — WYT bands stay
   A's (note this somewhere; comparing hist vs cc95 the year types differ).
Difference view (flow deltas as red/blue line coloring, storage delta circles) is v2;
decide after the toggle ships.

Open design questions for Eric: (a) flip-the-map toggle vs side-by-side synced maps
(recommend flip; side-by-side doubles particle/canvas cost and halves map size);
(b) default B = same theme's other hydrology, or same hydrology's baseline? (once
s0047/s0056 arrive, baseline-of-same-hydrology is the principled default);
(c) does B persist across mode switches / URL hash so links can share a comparison?

## Minor arcs — zoom-gated tributaries & distribution canals (July 5, 2026)

332 additional arcs (`marcs` payload key, `m:1` flag) drawn only at zoom ≥ 9 (`MINOR_MINZOOM`), muted colors (`MCOLORS`), ~half width scale, no particles, same tooltips/click-charts. Selection in `rebuild_data.py`: every gpkg CH arc with a CHANNEL series in the CSV not already on the map, kept if mean flow > 100 cfs OR peak |flow| > 1,000 cfs (mean catches steady tributaries, peak catches seasonal canals). Names from gpkg `NAME` (330/333 populated; fallback `Channel C_XXX`); river/canal/bypass class from `Sub_Type` (ST/CL/BP; NS=penstock→canal; NA→by name). **`C_CHCGO` is explicitly excluded** — unnamed 90-byte stub geometry with 22,000 cfs mean "flow", clearly a virtual/closure arc; check for others like it if the filter changes. CSV gotcha: the same `C_*` b-part appears under several c-parts (CHANNEL, FLOW-MIN-INSTREAM, DEBUG-CFS…) — minors use a c-part-filtered column map (`chanup`). `qref` is still computed from major arcs only, so major widths are unchanged. Payload 4.9→6.4 MB, HTML ~6.5 MB. Layers are added/removed from the map on `zoomend` (not style-toggled — canvas hit-testing follows automatically).

## Scope decision — v1 feature freeze (July 5, 2026)

Eric's call after the minor-arcs build: **no new data layers for now** — the map answers its core public-audience questions and each addition costs hover clutter and payload (6.5 MB, phone-relevant). Stopping criterion for any future layer: *does it answer a question a first-time public viewer actually arrives with that the current map can't?* By that test: environmental min-flows, scenario comparison, and groundwater pumping pass; more nodes/arcs/diversions fail. A broad diversions layer was considered and rejected — the minor canals already carry those time series; the only diversion candidate worth keeping is a **curated set of ~6–10 urban intake points** (CCC→CCWD, NBA, SBA, Freeport — places where the receiving conveyance isn't an arc in this export), styled like small pump triangles. Before any new layers: reservoir labels, small-reservoir clutter cleanup, CARTO licensing, then feedback from the COEQWAL team + a couple of first-time viewers to drive what's next.

## Remaining improvements (discussed, not yet built)

1. **Second scenario comparison** — A/B toggle or difference view ("what if"), which is the point of COEQWAL. **Deferred (July 2026):** scenario data will move from large CSV exports to a database; hold until that connectivity exists rather than building CSV-merge plumbing that gets replaced. Design discussion so far favors phased approach: A/B toggle + dual-scenario click-charts first, difference view later.
2. **Environmental context** — minimum-instream-flow requirement variables (`FLOW-MIN-INSTREAM` type) vs actual flow on key reaches; relevant to the salmon/ecological audience.
3. ~~**About panel**~~ — **done July 5, 2026.** Auto-opens on load; compact single panel with "simulated, not observed" caveat, 6-item visual key, story-button nudge, COEQWAL/DWR/CARTO credits + repo link. Reopens via About button in title panel; closes via ×, Esc, backdrop click, or "Explore the map" button. Lives in `build/make_html.py` template (search `aboutwrap`).
4. **Basemap licensing** — verify CARTO tile usage terms or self-host tiles for a public site. (~~Mobile pass~~ done July 5, 2026 — see Mobile pass section; still needs a real-phone live check after push.)
5. **Reservoir labels** at higher zoom levels for the major reservoirs.
6. **Filter or cluster the smallest reservoirs** (many of the 62 are tiny high-Sierra pools that clutter at statewide zoom).
7. **Video export** — render frames to MP4 for social media (or a Blender import pipeline for a 3D rendered version, given the Blender 5 workflow).
8. **Groundwater pumping** (`GP_*` variables) as a complement to the surface-delivery choropleth.
9. **Delta Cross Channel / additional Delta channels** if a future CSV export includes them.

## Mobile pass (July 5, 2026, late evening)

At ≤700px: simple mode becomes a **bottom sheet** (map on top ~45%, sheet max-height 52vh, legend collapsed behind a "Breakdown ▾" toggle; `sFit()` pads the camera by sheet height). Detailed mode gets a **compact header** (subtitle hidden, story buttons in a horizontal-scroll row, title clears the Big picture button), Leaflet zoom buttons hidden (pinch works), and the `#ctrl` row wraps so the month label no longer clips. **CSS gotcha:** the phone rules for `#simplepanel`/`#skeytoggle` live in a *second* media block at the END of the stylesheet — equal specificity, so source order against the base rules decides; putting them in the early media block silently loses. Verify with `python3 build/screenshot_mobile.py` (5 shots at 390×844) alongside the desktop harness. Not yet live-checked on a real phone (Chrome `resize_window` was a no-op on Eric's fullscreen/managed window — check live after next push).

## Screenshot verification harness (July 5, 2026)

The map can be visually verified headlessly (works in the Claude sandbox, no root needed):

1. `bash build/sandbox_setup.sh` — once per environment: installs playwright + Chromium, builds a stub `libXdamage.so.1` (Chromium links it but never calls it headless).
2. `LD_LIBRARY_PATH=$HOME/stublibs PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1 python3 build/screenshot.py [outdir]` — writes three PNGs (about panel, statewide, Delta close-up at Oct 1976) and fails on any page error.

Sandbox proxy blocks cdnjs/CARTO from inside the browser, so the harness serves Leaflet from `build/vendor/` (leaflet.js/css 1.9.4, vendored via npm) and aborts tile requests — gray background, all data layers render. In the sandbox, the stub lives at `/sessions/<name>/stublibs` (home dir doesn't persist between sessions; re-run setup each session).

## Verification history

Every layer was spot-checked against the raw CSV after each build (values, dates, signs, unit conversions) — all matched. JS syntax checked with `node --check` after each edit.
