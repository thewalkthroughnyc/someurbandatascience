import pandas as pd
import pytest

from bedford_corridor.ingest.crashes import (
    clean_crashes,
    clean_person,
    filter_cyclist_rows,
    join_crashes_person,
)


def test_clean_crashes_coerces_dtypes():
    raw = pd.DataFrame(
        {
            "collision_id": ["123", "456"],
            "crash_date": ["2025-01-01T00:00:00.000", "2025-02-01T00:00:00.000"],
            "latitude": ["40.69", "40.70"],
            "longitude": ["-73.95", "-73.96"],
            "number_of_cyclist_injured": ["1", None],
        }
    )

    out = clean_crashes(raw)

    assert out["collision_id"].dtype == "string"
    assert pd.api.types.is_datetime64_any_dtype(out["crash_date"])
    assert out["latitude"].dtype == float
    assert out["number_of_cyclist_injured"].dtype == "Int64"
    # missing injury count must stay missing, not become 0
    assert pd.isna(out["number_of_cyclist_injured"].iloc[1])


def test_clean_crashes_empty_passthrough():
    assert clean_crashes(pd.DataFrame()).empty


def test_clean_person_coerces_dtypes():
    raw = pd.DataFrame(
        {
            "collision_id": ["123"],
            "crash_date": ["2025-01-01T00:00:00.000"],
            "person_age": ["34"],
        }
    )

    out = clean_person(raw)

    assert out["collision_id"].dtype == "string"
    assert pd.api.types.is_datetime64_any_dtype(out["crash_date"])
    assert out["person_age"].dtype == "Int64"


def test_filter_cyclist_rows():
    person = pd.DataFrame(
        {
            "collision_id": ["1", "1", "2"],
            "person_type": ["Bicyclist", "Occupant", "Pedestrian"],
        }
    )

    out = filter_cyclist_rows(person)

    assert len(out) == 1
    assert out.iloc[0]["person_type"] == "Bicyclist"


def test_join_crashes_person_raises_on_duplicate_collision_id():
    crashes = pd.DataFrame({"collision_id": pd.array(["1", "1"], dtype="string")})
    person = pd.DataFrame({"collision_id": pd.array(["1"], dtype="string")})

    with pytest.raises(ValueError, match="duplicate collision_id"):
        join_crashes_person(crashes, person)


def test_join_crashes_person_narrows_person_to_corridor():
    # crashes_df is already bbox-filtered to the corridor; person_df is
    # citywide. Person rows for crashes outside the corridor must drop out.
    crashes = pd.DataFrame({"collision_id": pd.array(["1", "2"], dtype="string")})
    person = pd.DataFrame(
        {
            "collision_id": pd.array(["1", "2", "999-outside-corridor"], dtype="string"),
            "person_type": ["Bicyclist", "Occupant", "Bicyclist"],
        }
    )

    out = join_crashes_person(crashes, person)

    assert set(out["collision_id"]) == {"1", "2"}
    assert len(out) == 2


def test_join_crashes_person_keeps_crash_with_no_person_match():
    crashes = pd.DataFrame({"collision_id": pd.array(["1", "2"], dtype="string")})
    person = pd.DataFrame(
        {"collision_id": pd.array(["1"], dtype="string"), "person_type": ["Bicyclist"]}
    )

    out = join_crashes_person(crashes, person)

    assert len(out) == 2
    assert out[out["collision_id"] == "2"]["person_type"].isna().all()
