# CalSim3 Central Valley Water Map

An interactive, single-file HTML map visualizing California's Central Valley water allocation system as simulated by CalSim3 (COEQWAL scenario s0020, L2020A), October 1921 – September 2021 monthly. Built for a public audience.

**View the map:** open `CalSim3_water_map.html` in any browser (internet required for basemap tiles and Leaflet CDN).

## Features

Flow-scaled river/canal/bypass lines, reservoir circles with capacity rings, animated flow-direction particles (red on reversal), Banks/Jones export triangles, demand-unit delivery choropleth, water-year-type timeline with month scrubber, four guided story tours, and click-any-feature 100-year charts.

## Rebuilding from source data

The two large source files are not committed (they exceed GitHub's file size limit):

- `s0020_coeqwal_calsim_output.csv` (~279 MB) — wide-format DSS export from COEQWAL scenario s0020
- `20221103v2_cs3_cvhydroregion.gpkg` (~268 MB) — CalSim3 arcs, nodes, and reservoirs (EPSG:3310)

Place both in the repo root, then:

```bash
pip install pyproj pyshp
python3 build/rebuild_data.py   # extracts geometry + time series → build/payload.json
python3 build/make_html.py      # injects payload → CalSim3_water_map.html
```

## Documentation

See `PROJECT_NOTES.md` for the full technical reference: join keys, sign conventions, verification history, tuning knobs, and the remaining-improvements list.

## Caveat

All values are **simulated model output**, not observed data.
