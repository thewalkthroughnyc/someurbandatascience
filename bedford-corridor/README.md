# Bedford Avenue Corridor

Block-by-block cyclist-safety strip map for Bedford Ave, Dean St to Flushing
Ave, Brooklyn — before/after the Jul–Aug 2025 partial removal of protected
bike lane between Willoughby Ave and Flushing Ave. See [METHODS.md](METHODS.md)
for the write-up (in progress) and `config/corridor.py` for every verified
fact this project relies on (dates, block list, dataset IDs — each with a
source comment).

## Quick start

```
make all      # venv + deps, then builds web/data/corridor.json
make serve    # http://localhost:8000
make test     # pytest — 11 failures are EXPECTED, see "Project status" below
```

`make all` does NOT fetch crash/Citi Bike data over the network by default —
see "Data setup" below. Right now it produces a valid site with block
identity/order/treated-flags/LTS populated and everything else marked
`"computed": false`, because the analytical stubs (below) haven't been filled
in yet. That's intentional, not broken — open the site and you'll see three
working view toggles and an honest "not yet computed" state instead of fake
numbers.

## Project status: what's built vs. what's stubbed

Built and tested (`src/bedford_corridor/`):
- `ingest/socrata.py`, `ingest/crashes.py` — NYPD crash + person data pull/clean
- `ingest/citibike.py` — Citi Bike monthly CSV reader, handles both column schemas
- `ingest/centerline.py` — OSM street geometry fetch
- `routing/osrm_client.py`, `routing/cache.py` — OSRM routing + sqlite cache
- `build_json.py` — pipeline orchestrator, degrades gracefully around stubs

Stubbed — signature + docstring + failing tests only, intentionally left for
Jordan to implement (see each file's docstring and `tests/test_*.py`):
- `segmentation.py` — `segment_corridor()`: turns cross-street list + centerline
  geometry into block-face records
- `denominator.py` — `attribute_trips_to_blocks()` / `trips_per_block()`: the
  exposure denominator (routed Citi Bike trips per block)
- `stats/did.py` — `estimate_did()`: the difference-in-differences estimator
- `stats/interval.py` — `small_count_interval()`: small-count confidence intervals

`make test` will show 11 failing tests until these are filled in — that's the
expected, designed state, not a bug. As each stub is implemented, the
corresponding tests turn green and `build_json.py` starts populating that
section of the JSON with no other wiring changes needed.

## Data setup

**Socrata (crashes/person):** fetched automatically by `build_json.py` once
segmentation is implemented (currently skipped — see "Project status").
Optional: set `SOCRATA_APP_TOKEN` to raise the rate limit.

**Citi Bike:** not auto-downloaded (the file list depends on which months you
want in the study window, which is your call once you're implementing the
denominator). Grab the relevant monthly zips from
[citibikenyc.com/system-data](https://citibikenyc.com/system-data) into
`data_cache/citibike/`, or use `ingest.citibike.download_monthly_csv()`.

## Routing setup (OSRM, cycling profile)

Public OSRM demo servers only route "driving." You need a self-hosted
instance built with the bicycle profile:

```bash
mkdir -p data_cache/osrm && cd data_cache/osrm
curl -O https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-extract -p /opt/bicycle.lua /data/new-york-latest.osm.pbf
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-partition /data/new-york-latest.osrm
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-customize /data/new-york-latest.osrm
docker run -t -i -p 5000:5000 -v "${PWD}:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/new-york-latest.osrm
```

Then `routing.osrm_client.route()` against `http://localhost:5000` (the
default — override with `OSRM_BASE_URL` if different).

## Repo layout

```
bedford-corridor/
├── config/
│   ├── corridor.py     verified facts: dates, block list, dataset IDs (all sourced)
│   └── lts.yaml         editable fieldwork data — level of traffic stress per block
├── src/bedford_corridor/
│   ├── ingest/           built: Socrata, Citi Bike, OSM centerline
│   ├── routing/          built: OSRM client + cache
│   ├── stats/            stubbed: did.py, interval.py
│   ├── segmentation.py   stubbed
│   ├── denominator.py    stubbed
│   └── build_json.py     orchestrator → web/data/corridor.json
├── tests/
├── web/                  static site: index.html, style.css, map.js — no build step
├── METHODS.md            headers + TODOs, prose to be written
└── Makefile
```
