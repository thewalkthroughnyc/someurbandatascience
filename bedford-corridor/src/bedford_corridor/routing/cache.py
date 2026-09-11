"""On-disk cache for OSRM routes, keyed by station pair.

Citi Bike trips concentrate onto a small number of station pairs relative to
trip volume — caching by (profile, start_station_id, end_station_id) turns
tens of thousands of trips into a few hundred unique OSRM calls. Backed by
sqlite (stdlib, no new dependency) so the cache survives across pipeline
runs and can be committed/shared if desired (it's small — geometry only,
not trip data).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Callable

from bedford_corridor.routing.osrm_client import Route

_SCHEMA = """
CREATE TABLE IF NOT EXISTS route_cache (
    profile TEXT NOT NULL,
    start_station_id TEXT NOT NULL,
    end_station_id TEXT NOT NULL,
    distance_m REAL NOT NULL,
    duration_s REAL NOT NULL,
    geometry_json TEXT NOT NULL,
    PRIMARY KEY (profile, start_station_id, end_station_id)
);
"""


class RouteCache:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def get(self, profile: str, start_station_id: str, end_station_id: str) -> Route | None:
        row = self._conn.execute(
            "SELECT distance_m, duration_s, geometry_json FROM route_cache "
            "WHERE profile = ? AND start_station_id = ? AND end_station_id = ?",
            (profile, start_station_id, end_station_id),
        ).fetchone()
        if row is None:
            return None
        distance_m, duration_s, geometry_json = row
        geometry = [tuple(pt) for pt in json.loads(geometry_json)]
        return Route(distance_m=distance_m, duration_s=duration_s, geometry=geometry)

    def put(self, profile: str, start_station_id: str, end_station_id: str, route_: Route) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO route_cache "
            "(profile, start_station_id, end_station_id, distance_m, duration_s, geometry_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                profile,
                start_station_id,
                end_station_id,
                route_.distance_m,
                route_.duration_s,
                json.dumps(route_.geometry),
            ),
        )
        self._conn.commit()

    def get_or_fetch(
        self,
        profile: str,
        start_station_id: str,
        end_station_id: str,
        fetch_fn: Callable[[], Route],
    ) -> Route:
        """Return the cached route for this station pair, or call fetch_fn()
        (expected to hit OSRM), cache the result, and return it.
        """
        cached = self.get(profile, start_station_id, end_station_id)
        if cached is not None:
            return cached
        route_ = fetch_fn()
        self.put(profile, start_station_id, end_station_id, route_)
        return route_

    def close(self) -> None:
        self._conn.close()
