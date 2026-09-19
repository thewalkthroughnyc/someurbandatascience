"""02 — Network walk times.

Run:  python src/02_walk_times.py          (or: make walktimes)

For every band tract: minutes on the walk network from the tract's internal
point to (a) the nearest M-only station — Ridgewood/Middle Village, the
subject — and, as controls, (b) the nearest full-service non-L station and
(c) the nearest L station. Holding the other two fixed is what lets the M
coefficient mean "near the M-only cluster" rather than "near some train."

Method: snap stations and tract points to graph nodes, then ONE
multi-source Dijkstra per station set — every tract's distance to its
nearest station in that set falls out of a single pass. Network distance,
not straight-line: the Bushwick/Ridgewood grid and the Cemetery of the
Evergreens make the two diverge sharply, and that divergence is the
contribution.

Heads-up: the Overpass download + graph build for ~60 km^2 of dense
Brooklyn/Queens is the slow step — expect 10-30 min the first time.
OSMnx caches, so reruns are fast.
"""

from __future__ import annotations

import time

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd

import config as C

ox.settings.use_cache = True
ox.settings.cache_folder = str(C.RAW / "osmnx_cache")
ox.settings.log_console = True


def snap(G, gdf_proj):
    """Nearest graph nodes for a projected GeoDataFrame. Returns (nodes, snap_m)."""
    nodes, dist_units = ox.distance.nearest_nodes(
        G, gdf_proj.geometry.x.values, gdf_proj.geometry.y.values, return_dist=True
    )
    # Graph is projected to EPSG:2263 -> snap distances come back in FEET.
    return np.asarray(nodes), np.asarray(dist_units) * C.M_PER_FT


def main() -> None:
    t0 = time.time()
    tracts = gpd.read_file(C.PROCESSED / f"band_tracts{C.SPINE_TAG}.geojson")
    stations = gpd.read_file(C.PROCESSED / f"stations_band{C.SPINE_TAG}.geojson")
    band = gpd.read_file(C.PROCESSED / f"band{C.SPINE_TAG}.geojson")

    # --- build the graph over band + margin, in lat/lon for Overpass -----
    poly = (
        band.to_crs(C.EPSG_LOCAL)
        .buffer(C.GRAPH_MARGIN_MILES * C.FT_PER_MILE)
        .to_crs(4326)
        .iloc[0]
    )
    print("[1/3] Downloading + building the walk network (the slow step)...")
    G = ox.graph_from_polygon(poly, network_type="walk", simplify=True)
    Gp = ox.project_graph(G, to_crs=f"EPSG:{C.EPSG_LOCAL}")
    print(f"      {len(Gp.nodes):,} nodes / {len(Gp.edges):,} edges "
          f"({time.time() - t0:,.0f}s)")

    # --- snap everything --------------------------------------------------
    print("[2/3] Snapping stations and tract internal points to the network")
    st_proj = stations.to_crs(C.EPSG_LOCAL)
    tr_pts = gpd.GeoDataFrame(
        tracts[["GEOID"]],
        geometry=gpd.points_from_xy(tracts.intpt_lon, tracts.intpt_lat, crs=4326),
    ).to_crs(C.EPSG_LOCAL)

    st_nodes, _ = snap(Gp, st_proj)          # station snap error ~10-50 m; ignored
    tr_nodes, tr_snap_m = snap(Gp, tr_pts)

    src_M = set(st_nodes[st_proj.is_M_only.values])
    src_L = set(st_nodes[st_proj.is_L.values])
    src_full_nonL = set(st_nodes[(~st_proj.is_L.values) & (~st_proj.is_M_only.values)])
    print(f"      sources: {len(src_M)} M-only nodes (the subject); "
          f"{len(src_full_nonL)} full-service non-L and {len(src_L)} L nodes as controls")

    # --- one Dijkstra per station set ------------------------------------
    print("[3/3] Multi-source Dijkstra x3 (edge lengths are meters)")
    def dijkstra(sources):
        # An M-spine band can leave a control set with no stations in reach;
        # an empty source set means "no such station nearby" -> all NaN, and
        # fit_model drops that control automatically.
        return nx.multi_source_dijkstra_path_length(Gp, sources, weight="length") if sources else {}

    dist_M = dijkstra(src_M)
    dist_L = dijkstra(src_L)
    dist_nonL = dijkstra(src_full_nonL)

    def minutes(dist_map, node, snap_m):
        d = dist_map.get(node)
        if d is None:
            return np.nan
        return (d + snap_m) / C.WALK_SPEED_M_PER_MIN

    out = pd.DataFrame({
        "GEOID": tracts["GEOID"].values,
        "walk_M_min": [minutes(dist_M, n, s) for n, s in zip(tr_nodes, tr_snap_m)],
        "walk_L_min": [minutes(dist_L, n, s) for n, s in zip(tr_nodes, tr_snap_m)],
        "walk_nonL_min": [minutes(dist_nonL, n, s) for n, s in zip(tr_nodes, tr_snap_m)],
        "snap_m": tr_snap_m.round(1),
    })

    # label the (approx) nearest M-only station for the walk packet —
    # euclidean argmin, fine for a label, not used in the model
    m_st = st_proj[st_proj.is_M_only].reset_index(drop=True)
    mx, my = m_st.geometry.x.values, m_st.geometry.y.values
    tx, ty = tr_pts.geometry.x.values, tr_pts.geometry.y.values
    nearest_idx = np.argmin(
        (tx[:, None] - mx[None, :]) ** 2 + (ty[:, None] - my[None, :]) ** 2, axis=1
    )
    out["nearest_M_station"] = m_st["name"].values[nearest_idx]

    out.to_csv(C.PROCESSED / f"walk_times{C.SPINE_TAG}.csv", index=False)

    n_unreach = int(out["walk_M_min"].isna().sum())
    print(f"\nSaved data/processed/walk_times{C.SPINE_TAG}.csv")
    print(f"  median walk to nearest M-only station: {out.walk_M_min.median():5.1f} min")
    print(f"  (controls) median walk to full non-L:  {out.walk_nonL_min.median():5.1f} min")
    print(f"  (controls) median walk to L:           {out.walk_L_min.median():5.1f} min")
    print(f"  unreachable tracts:    {n_unreach}   "
          f"(become NaN; dropped + logged in 03)")
    print(f"  total: {time.time() - t0:,.0f}s")


if __name__ == "__main__":
    main()
