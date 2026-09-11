"""Exposure denominator — STUBBED.

Citi Bike gives station pairs, not routes. The plan (see METHODS.md) is:
route each unique station pair over the bike network via
routing.osrm_client.route() (cached by routing.cache.RouteCache — both
already built), then decide which corridor blocks each route's geometry
actually traverses, then turn that into a modeled trip-count denominator per
block per period. The routing+caching machinery is done; the attribution
and rate logic is the analytical core of this project and is left for you.
See tests/test_denominator.py for the behavior it needs to satisfy.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

from bedford_corridor.routing.cache import RouteCache


def attribute_trips_to_blocks(
    trips: pd.DataFrame,
    blocks: gpd.GeoDataFrame,
    route_cache: RouteCache,
    profile: str = "bike",
) -> pd.DataFrame:
    """For each trip in `trips` (normalized Citi Bike schema — see
    ingest.citibike.NORMALIZED_COLUMNS), look up its cached route geometry
    and determine which of `blocks` (segmentation.segment_corridor output)
    it actually crosses.

    Returns a long-format DataFrame: one row per (ride_id, block_id) pair
    for every block a trip traverses. A trip that never enters the corridor
    contributes zero rows, not a row with a null block_id.

    Decisions intentionally left open for you: how close a route geometry
    needs to pass to a block's line to count as "traversing" it (a routing
    buffer distance), and what to do with trips whose station pair has no
    cached route yet (fetch on demand here, or require pre-warming?).
    """
    raise NotImplementedError("attribute_trips_to_blocks is a stub — see METHODS.md")


def trips_per_block(
    attributed: pd.DataFrame,
    blocks: gpd.GeoDataFrame,
    period_start: "pd.Timestamp",
    period_end: "pd.Timestamp",
) -> pd.DataFrame:
    """Aggregate attribute_trips_to_blocks() output into a modeled
    trip-count denominator per block for [period_start, period_end).

    Returns one row per block_id with a `modeled_trips` column. This is
    where you decide how to handle blocks near-zero exposure (does a block
    with 3 modeled trips get a rate at all, or does it get suppressed the
    same way small-count crash numbers do in stats.interval?).
    """
    raise NotImplementedError("trips_per_block is a stub — see METHODS.md")
