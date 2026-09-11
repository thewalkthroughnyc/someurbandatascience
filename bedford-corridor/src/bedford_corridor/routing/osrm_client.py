"""HTTP client for a self-hosted OSRM instance running the bicycle profile.

Public OSRM demo servers (router.project-osrm.org) only serve the "driving"
profile — routing Citi Bike trips over the street network for this study
requires a self-hosted OSRM built with bicycle.lua. See README.md "Routing
setup" for the docker-compose command that builds one from a NYC OSM extract.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests


class OSRMError(RuntimeError):
    pass


@dataclass(frozen=True)
class Route:
    distance_m: float
    duration_s: float
    # Ordered list of (lat, lng) points along the route geometry.
    geometry: list[tuple[float, float]]


def route(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    base_url: str,
    profile: str = "bike",
    session: requests.Session | None = None,
) -> Route:
    """Query OSRM's /route service for the shortest path between two points
    under the given profile. Coordinates in, coordinates out are (lat, lng)
    — OSRM's own API is (lng, lat), the flip happens inside this function so
    nothing upstream has to remember OSRM's convention.
    """
    session = session or requests.Session()
    url = f"{base_url}/route/v1/{profile}/{start_lng},{start_lat};{end_lng},{end_lat}"
    params = {"geometries": "geojson", "overview": "full"}

    try:
        resp = session.get(url, params=params, timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise OSRMError(
            f"Could not reach OSRM at {base_url}. Is a bicycle-profile OSRM instance "
            "running? See README.md 'Routing setup'."
        ) from e

    resp.raise_for_status()
    payload = resp.json()

    if payload.get("code") != "Ok":
        raise OSRMError(f"OSRM returned {payload.get('code')}: {payload.get('message')}")

    leg = payload["routes"][0]
    coords = leg["geometry"]["coordinates"]  # [[lng, lat], ...]
    return Route(
        distance_m=leg["distance"],
        duration_s=leg["duration"],
        geometry=[(lat, lng) for lng, lat in coords],
    )
