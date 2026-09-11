"""Block segmentation — STUBBED. This is analytical/geometric judgment
(where exactly a block boundary falls, how to handle the Monroe/Gates
gap flagged in config/corridor.py, what geometry source to trust) and is
intentionally left for you to implement. See tests/test_segmentation.py for
the behavior it needs to satisfy.
"""

from __future__ import annotations

import geopandas as gpd


def segment_corridor(
    cross_streets: list[str],
    treated_blocks: list[tuple[str, str]],
    centerline_source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Split the corridor into one block-face record per consecutive pair of
    cross streets in `cross_streets`.

    Parameters
    ----------
    cross_streets : ordered list of cross-street names, south to north
        (config.corridor.CROSS_STREETS).
    treated_blocks : (from_street, to_street) pairs marking which blocks lost
        protection (config.corridor.TREATED_BLOCKS).
    centerline_source : street centerline geometry (e.g. NYC LION, loaded
        upstream) to derive each block's line geometry from.

    Returns
    -------
    GeoDataFrame, one row per block, columns:
        block_id : str, stable identifier (e.g. "{from_street}__{to_street}"
                   slugified — must match config/lts.yaml block ids)
        sequence_number : int, 0-indexed position south to north
        from_street, to_street : str
        is_treated : bool
        geometry : LineString for that block face

    Must raise ValueError (not silently drop or merge) if a cross street in
    `cross_streets` has no matching intersection in `centerline_source` —
    a silently skipped block is worse than a loud failure here.
    """
    raise NotImplementedError("segment_corridor is a stub — see METHODS.md")
