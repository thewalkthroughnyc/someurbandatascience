"""01 — Define the band, pull the rent.

Run:  python src/01_pull_acs.py            (or: make pull)

Does four things and prints Gate 1 at the end:
  1. MTA stations  -> L corridor line (Bedford Av .. Canarsie) -> band polygon
  2. TIGER tracts for Kings + Queens -> keep those whose internal point
     falls inside the band
  3. ACS 2020-2024 5-year pull (median gross rent + controls) for both counties
  4. Save processed GeoJSONs + print the Gate 1 count

Downloads are cached in data/raw/ — reruns are offline after the first pass.
"""

from __future__ import annotations

import os
import sys

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

import config as C
import lib

KEY_SIGNUP = "https://api.census.gov/data/key_signup.html"


# ---------------------------------------------------------------- helpers


def cached_download(url: str, dest, desc: str):
    if dest.exists():
        print(f"  [cached] {desc}: {dest.name}")
        return dest
    print(f"  [fetch]  {desc}: {url}")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def fetch_stations() -> pd.DataFrame:
    path = cached_download(C.STATIONS_URL, C.RAW / "mta_stations.csv", "MTA subway stations")
    df = pd.read_csv(path)
    cols = {
        "name": lib.pick_col(df, "stop", "name"),
        "routes": lib.pick_col(df, "daytime"),
        "borough": lib.pick_col(df, "borough"),
        "gtfs_id": lib.pick_col(df, "gtfs", "stop", "id"),
        "lat": lib.pick_col(df, "gtfs", "lat"),
        "lon": lib.pick_col(df, "gtfs", "lon"),
    }
    out = df[[cols[k] for k in cols]].copy()
    out.columns = list(cols)
    out["is_L"] = out["routes"].apply(lambda r: lib.has_route(r, "L"))
    return out


def acs_pull(year: int) -> pd.DataFrame:
    """One request per county. Falls back a vintage if the year 404s."""
    base = f"https://api.census.gov/data/{year}/acs/acs5"
    varlist = ",".join(["NAME"] + list(C.ACS_VARS))
    key = os.environ.get("CENSUS_API_KEY", "").strip()

    frames = []
    for county in C.COUNTY_FIPS:
        params = [("get", varlist), ("for", "tract:*"),
                  ("in", f"state:{C.STATE_FIPS}"), ("in", f"county:{county}")]
        if key:
            params.append(("key", key))
        r = requests.get(base, params=params, timeout=120)
        if r.status_code == 404:
            raise FileNotFoundError(year)
        if r.status_code in (401, 403) or "key" in r.text[:400].lower() and r.status_code >= 400:
            sys.exit(
                f"\nCensus API rejected the request (HTTP {r.status_code}).\n"
                f"The API now requires a key for all queries. Get one (free, ~instant):\n"
                f"  {KEY_SIGNUP}\n"
                f"then:  export CENSUS_API_KEY=yourkey  and rerun.\n"
            )
        r.raise_for_status()
        rows = r.json()
        frames.append(pd.DataFrame(rows[1:], columns=rows[0]))
    df = pd.concat(frames, ignore_index=True)

    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    for var, name in C.ACS_VARS.items():
        df[name] = lib.to_numeric_acs(df[var])
    keep = ["GEOID", "NAME"] + list(C.ACS_VARS.values())
    return df[keep]


# ---------------------------------------------------------------- main

def main() -> None:
    C.RAW.mkdir(parents=True, exist_ok=True)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)

    # --- 1. stations -> corridor -> band -------------------------------
    print("\n[1/4] Stations and the band")
    st = fetch_stations()
    st_gdf = gpd.GeoDataFrame(
        st, geometry=[Point(xy) for xy in zip(st.lon, st.lat)], crs=4326
    ).to_crs(C.EPSG_LOCAL)

    l_bk = st_gdf[st_gdf.is_L & (st_gdf.borough == "Bk")].sort_values("gtfs_id")
    if len(l_bk) < 10:
        sys.exit(f"Expected ~19 Brooklyn L stations, found {len(l_bk)} — "
                 "check the Borough / Daytime Routes columns in data/raw/mta_stations.csv")
    print(f"  Brooklyn L stations found: {len(l_bk)} "
          f"({l_bk.iloc[0]['name']} .. {l_bk.iloc[-1]['name']})")

    corridor = lib.corridor_line(list(zip(l_bk.geometry.x, l_bk.geometry.y)))
    band = lib.band_polygon(corridor, C.BAND_RADIUS_MILES * C.FT_PER_MILE)

    # Stations relevant to the analysis: everything in/near the band.
    near = st_gdf[st_gdf.geometry.distance(band) <= C.NONL_STATION_MARGIN_MILES * C.FT_PER_MILE].copy()
    print(f"  Stations in/near band: {len(near)} "
          f"({int(near.is_L.sum())} L, {int((~near.is_L).sum())} non-L for the control)")

    # --- 2. tracts ------------------------------------------------------
    print("\n[2/4] TIGER tracts (NY state file, filtered to Kings + Queens)")
    tiger = cached_download(C.TIGER_URL, C.RAW / "tl_2024_36_tract.zip", "TIGER 2024 tracts")
    tr = gpd.read_file(tiger)
    tr = tr[tr["COUNTYFP"].isin(C.COUNTY_FIPS)].copy()
    tr["intpt_lat"] = tr["INTPTLAT"].astype(float)
    tr["intpt_lon"] = tr["INTPTLON"].astype(float)
    tr = tr.to_crs(C.EPSG_LOCAL)

    ip = gpd.GeoSeries([Point(xy) for xy in zip(tr.intpt_lon, tr.intpt_lat)], crs=4326).to_crs(C.EPSG_LOCAL)
    inside = lib.points_in_polygon(ip.x.values, ip.y.values, band)
    tr = tr[inside].copy()
    print(f"  Tracts with internal point inside the {C.BAND_RADIUS_MILES}-mile band: {len(tr)}")

    # --- 3. ACS ---------------------------------------------------------
    print(f"\n[3/4] ACS {C.ACS_YEAR - 4}-{C.ACS_YEAR} 5-year pull (B25064 + controls)")
    try:
        acs = acs_pull(C.ACS_YEAR)
        vintage = C.ACS_YEAR
    except FileNotFoundError:
        print(f"  {C.ACS_YEAR} vintage not on the API yet — falling back to {C.ACS_YEAR - 1}")
        acs = acs_pull(C.ACS_YEAR - 1)
        vintage = C.ACS_YEAR - 1

    merged = tr.drop(columns=["NAME"]).merge(acs, on="GEOID", how="left", validate="1:1")
    merged["acs_vintage"] = vintage

    # --- 4. save + Gate 1 ----------------------------------------------
    print("\n[4/4] Saving processed layers")
    keep = ["GEOID", "NAME", "intpt_lat", "intpt_lon", "ALAND", "acs_vintage",
            *C.ACS_VARS.values(), "geometry"]
    band_tracts = merged[keep].to_crs(4326)
    band_tracts.to_file(C.PROCESSED / "band_tracts.geojson", driver="GeoJSON")
    gpd.GeoDataFrame(geometry=[band], crs=C.EPSG_LOCAL).to_crs(4326).to_file(
        C.PROCESSED / "band.geojson", driver="GeoJSON")
    near.to_crs(4326).to_file(C.PROCESSED / "stations_band.geojson", driver="GeoJSON")
    print("  data/processed/band_tracts.geojson  (tract polygons + ACS attrs)")
    print("  data/processed/band.geojson         (the band — the p5 sketch can use this)")
    print("  data/processed/stations_band.geojson")

    n_total = len(band_tracts)
    n_rent = int(band_tracts["med_rent"].notna().sum())
    n_usable = int(((band_tracts["med_rent"].notna())
                    & (band_tracts["renter_hh"].fillna(0) >= C.MIN_RENTER_HH)).sum())

    print("\n" + "=" * 62)
    print(f" GATE 1 — SAMPLE            (ACS {vintage - 4}-{vintage}, band {C.BAND_RADIUS_MILES} mi)")
    print("=" * 62)
    print(f"  Tracts in band:                        {n_total:5d}")
    print(f"  ... with a median-rent estimate:       {n_rent:5d}")
    print(f"  ... and >= {C.MIN_RENTER_HH} renter households:      {n_usable:5d}")
    if n_usable >= C.GATE1_COMFORTABLE_N:
        print(f"\n  Comfortable (suggested floor: {C.GATE1_COMFORTABLE_N}). Proceed to 02.")
    else:
        print(f"\n  Thin (suggested floor: {C.GATE1_COMFORTABLE_N}). Widen the band now, not in week 3:")
        print("    edit BAND_RADIUS_MILES in src/config.py and rerun this script.")
    print("  The gate decision is yours — this is the input to it.")
    print("=" * 62)


if __name__ == "__main__":
    main()
