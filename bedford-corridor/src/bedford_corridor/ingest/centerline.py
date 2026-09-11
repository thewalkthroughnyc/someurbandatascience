"""Fetch street centerline geometry from OpenStreetMap (Overpass API).

Boilerplate data-fetch, not analysis: this hands segmentation.segment_corridor()
raw geometry to work with. It does NOT decide where block boundaries are —
that's the stubbed part. Uses OSM/Overpass rather than NYC's LION shapefile
because it needs no large file download and is queryable directly by street
name + bbox; the segmentation stub's docstring flags that its output should
still be spot-checked against LION before trusting it.
"""

from __future__ import annotations

import geopandas as gpd
import requests
from shapely.geometry import LineString, Point

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# Overpass 406s requests carrying the default python-requests User-Agent;
# needs something that identifies the client.
_HEADERS = {"User-Agent": "bedford-corridor-research/0.1"}


def _build_query(bbox: dict[str, float]) -> str:
    box = f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}"
    return f"[out:json][timeout:60];way[\"highway\"][\"name\"]({box});out geom;"


def fetch_named_streets(bbox: dict[str, float], session: requests.Session | None = None) -> gpd.GeoDataFrame:
    """Return every named street way inside `bbox` as a GeoDataFrame of
    LineStrings, one row per OSM way (a real street is often split across
    several ways — callers that need one geometry per street name should
    group/merge downstream).
    """
    session = session or requests.Session()
    resp = session.get(OVERPASS_URL, params={"data": _build_query(bbox)}, headers=_HEADERS, timeout=90)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])

    records = []
    for el in elements:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        name = el.get("tags", {}).get("name")
        if not name:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
        if len(coords) < 2:
            continue
        records.append({"name": name, "osm_id": el["id"], "geometry": LineString(coords)})

    return gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")


def fetch_intersection_points(
    corridor_street: str, bbox: dict[str, float], session: requests.Session | None = None
) -> gpd.GeoDataFrame:
    """Return named-intersection nodes along `corridor_street` inside `bbox`
    (Overpass nodes tagged e.g. "Bedford Avenue & Willoughby Avenue"), as a
    GeoDataFrame of Points with a `cross_street` column. This is the same
    approach used to verify the block list in config/corridor.py by hand —
    exposed here as a real function so segmentation can call it instead of
    the analysis re-deriving it from scratch.
    """
    session = session or requests.Session()
    box = f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}"
    query = f'[out:json][timeout:60];node["name"~"^{corridor_street} & "]({box});out;'
    resp = session.get(OVERPASS_URL, params={"data": query}, headers=_HEADERS, timeout=90)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])

    prefix = f"{corridor_street} & "
    records = []
    for el in elements:
        if el.get("type") != "node":
            continue
        name = el.get("tags", {}).get("name", "")
        if not name.startswith(prefix):
            continue
        records.append(
            {
                "cross_street": name[len(prefix):],
                "geometry": Point(el["lon"], el["lat"]),
            }
        )

    return gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
