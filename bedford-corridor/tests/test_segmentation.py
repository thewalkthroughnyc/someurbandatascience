"""segmentation.segment_corridor is a STUB (see src/bedford_corridor/segmentation.py).
These tests fail until it's implemented — that's expected. They encode the
shape/behavior the real implementation needs to satisfy.
"""

import geopandas as gpd
import pytest

from config.corridor import CROSS_STREETS, TREATED_BLOCKS

from bedford_corridor.segmentation import segment_corridor


def test_segment_corridor_is_currently_a_stub():
    with pytest.raises(NotImplementedError):
        segment_corridor(CROSS_STREETS, TREATED_BLOCKS, centerline_source=gpd.GeoDataFrame())


def test_segment_corridor_produces_one_block_per_consecutive_cross_street_pair():
    result = segment_corridor(CROSS_STREETS, TREATED_BLOCKS, centerline_source=gpd.GeoDataFrame())

    assert len(result) == len(CROSS_STREETS) - 1
    assert list(result["from_street"]) == CROSS_STREETS[:-1]
    assert list(result["to_street"]) == CROSS_STREETS[1:]


def test_segment_corridor_flags_exactly_the_treated_blocks():
    result = segment_corridor(CROSS_STREETS, TREATED_BLOCKS, centerline_source=gpd.GeoDataFrame())

    treated = result[result["is_treated"]]
    assert len(treated) == len(TREATED_BLOCKS)
    assert set(zip(treated["from_street"], treated["to_street"])) == set(TREATED_BLOCKS)


def test_segment_corridor_raises_on_cross_street_missing_from_centerline():
    with pytest.raises(ValueError):
        segment_corridor(
            ["Not A Real Street", "Also Not Real"],
            [],
            centerline_source=gpd.GeoDataFrame(),
        )
