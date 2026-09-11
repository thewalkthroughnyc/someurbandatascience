from unittest.mock import MagicMock

from bedford_corridor.ingest.centerline import fetch_intersection_points, fetch_named_streets

BBOX = {"min_lat": 40.67, "max_lat": 40.70, "min_lon": -73.96, "max_lon": -73.95}


def _mock_response(elements):
    resp = MagicMock()
    resp.json.return_value = {"elements": elements}
    resp.raise_for_status.return_value = None
    return resp


def test_fetch_named_streets_builds_linestrings():
    session = MagicMock()
    session.get.return_value = _mock_response(
        [
            {
                "type": "way",
                "id": 1,
                "tags": {"name": "Bedford Avenue"},
                "geometry": [{"lat": 40.69, "lon": -73.95}, {"lat": 40.70, "lon": -73.96}],
            },
            {"type": "way", "id": 2, "tags": {}, "geometry": [{"lat": 1, "lon": 1}]},  # no name, skipped
        ]
    )

    out = fetch_named_streets(BBOX, session=session)

    assert len(out) == 1
    assert out.iloc[0]["name"] == "Bedford Avenue"


def test_fetch_intersection_points_parses_cross_street_name():
    session = MagicMock()
    session.get.return_value = _mock_response(
        [
            {
                "type": "node",
                "tags": {"name": "Bedford Avenue & Willoughby Avenue"},
                "lat": 40.6934,
                "lon": -73.9558,
            }
        ]
    )

    out = fetch_intersection_points("Bedford Avenue", BBOX, session=session)

    assert len(out) == 1
    assert out.iloc[0]["cross_street"] == "Willoughby Avenue"
