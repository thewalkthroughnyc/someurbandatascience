import zipfile

import pandas as pd
import pytest

from bedford_corridor.ingest.citibike import (
    detect_schema,
    filter_near_corridor,
    normalize,
    read_monthly_csv,
)

CURRENT_ROW = {
    "ride_id": "abc123",
    "rideable_type": "classic_bike",
    "started_at": "2025-01-01 08:00:00",
    "ended_at": "2025-01-01 08:15:00",
    "start_station_name": "Bedford Ave & Myrtle Ave",
    "start_station_id": "5001",
    "end_station_name": "Bedford Ave & Willoughby Ave",
    "end_station_id": "5002",
    "start_lat": 40.6946,
    "start_lng": -73.9561,
    "end_lat": 40.6934,
    "end_lng": -73.9558,
    "member_casual": "member",
}

LEGACY_ROW = {
    "tripduration": "600",
    "starttime": "2019-01-01 08:00:00",
    "stoptime": "2019-01-01 08:10:00",
    "start station id": "5001",
    "start station name": "Bedford Ave & Myrtle Ave",
    "start station latitude": "40.6946",
    "start station longitude": "-73.9561",
    "end station id": "5002",
    "end station name": "Bedford Ave & Willoughby Ave",
    "end station latitude": "40.6934",
    "end station longitude": "-73.9558",
    "bikeid": "12345",
    "usertype": "Subscriber",
    "birth year": "1990",
    "gender": "1",
}


def test_detect_schema_current():
    assert detect_schema(list(CURRENT_ROW.keys())) == "current"


def test_detect_schema_legacy():
    assert detect_schema(list(LEGACY_ROW.keys())) == "legacy"


def test_detect_schema_unrecognized_raises():
    with pytest.raises(ValueError, match="Unrecognized"):
        detect_schema(["some", "other", "columns"])


def test_normalize_current_schema():
    df = pd.DataFrame([CURRENT_ROW])

    out = normalize(df)

    assert out.loc[0, "ride_id"] == "abc123"
    assert out.loc[0, "start_station_id"] == "5001"
    assert pd.api.types.is_datetime64_any_dtype(out["started_at"])


def test_normalize_legacy_schema_synthesizes_ride_id():
    df = pd.DataFrame([LEGACY_ROW])

    out = normalize(df)

    assert out.loc[0, "start_station_id"] == "5001"
    assert out.loc[0, "member_casual"] == "Subscriber"
    assert pd.notna(out.loc[0, "ride_id"])
    assert out.loc[0, "ride_id"] != ""


def test_normalize_empty_returns_empty_with_columns():
    out = normalize(pd.DataFrame())
    assert out.empty
    assert list(out.columns) != []


def test_filter_near_corridor():
    bbox = {"min_lat": 40.690, "max_lat": 40.700, "min_lon": -73.960, "max_lon": -73.950}
    df = pd.DataFrame(
        [
            {"start_lat": 40.695, "start_lng": -73.955, "end_lat": 40.500, "end_lng": -73.900},
            {"start_lat": 40.500, "start_lng": -73.900, "end_lat": 40.500, "end_lng": -73.900},
        ]
    )

    out = filter_near_corridor(df, bbox)

    assert len(out) == 1


def test_read_monthly_csv_handles_zip(tmp_path):
    csv_path = tmp_path / "202501-citibike-tripdata.csv"
    pd.DataFrame([CURRENT_ROW]).to_csv(csv_path, index=False)

    zip_path = tmp_path / "202501-citibike-tripdata.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(csv_path, arcname=csv_path.name)

    out = read_monthly_csv(zip_path)

    assert len(out) == 1
    assert out.loc[0, "ride_id"] == "abc123"
