"""denominator.attribute_trips_to_blocks / trips_per_block are STUBS (see
src/bedford_corridor/denominator.py). These tests fail until implemented —
expected. They encode the shape/behavior the real implementation needs.
"""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString

from bedford_corridor.denominator import attribute_trips_to_blocks, trips_per_block
from bedford_corridor.routing.cache import RouteCache


@pytest.fixture
def fake_blocks():
    return gpd.GeoDataFrame(
        {
            "block_id": ["willoughby_myrtle", "myrtle_park"],
            "geometry": [
                LineString([(-73.9558, 40.6934), (-73.9561, 40.6946)]),
                LineString([(-73.9561, 40.6946), (-73.9565, 40.6967)]),
            ],
        },
        crs="EPSG:4326",
    )


@pytest.fixture
def fake_trips():
    return pd.DataFrame(
        {
            "ride_id": ["r1", "r2"],
            "start_station_id": ["5001", "9001"],
            "end_station_id": ["5002", "9002"],
        }
    )


def test_attribute_trips_to_blocks_is_currently_a_stub(fake_trips, fake_blocks, tmp_path):
    cache = RouteCache(tmp_path / "routes.sqlite")
    with pytest.raises(NotImplementedError):
        attribute_trips_to_blocks(fake_trips, fake_blocks, cache)


def test_attribute_trips_to_blocks_returns_long_format(fake_trips, fake_blocks, tmp_path):
    cache = RouteCache(tmp_path / "routes.sqlite")
    out = attribute_trips_to_blocks(fake_trips, fake_blocks, cache)
    assert set(out.columns) >= {"ride_id", "block_id"}


def test_attribute_trips_to_blocks_excludes_non_corridor_trips(fake_blocks, tmp_path):
    # a trip entirely elsewhere in the city should contribute zero rows,
    # not a row with a null/placeholder block_id
    trips = pd.DataFrame({"ride_id": ["far_away"], "start_station_id": ["1"], "end_station_id": ["2"]})
    cache = RouteCache(tmp_path / "routes.sqlite")
    out = attribute_trips_to_blocks(trips, fake_blocks, cache)
    assert "far_away" not in set(out["ride_id"])


def test_trips_per_block_is_currently_a_stub(fake_blocks):
    attributed = pd.DataFrame({"ride_id": ["r1"], "block_id": ["willoughby_myrtle"]})
    with pytest.raises(NotImplementedError):
        trips_per_block(attributed, fake_blocks, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01"))


def test_trips_per_block_returns_one_row_per_block(fake_blocks):
    attributed = pd.DataFrame(
        {"ride_id": ["r1", "r2", "r3"], "block_id": ["willoughby_myrtle", "willoughby_myrtle", "myrtle_park"]}
    )
    out = trips_per_block(attributed, fake_blocks, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01"))
    assert set(out["block_id"]) == set(fake_blocks["block_id"])
    assert out.set_index("block_id").loc["willoughby_myrtle", "modeled_trips"] == 2
