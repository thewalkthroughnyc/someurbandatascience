from unittest.mock import MagicMock

import pytest

from bedford_corridor.routing.cache import RouteCache
from bedford_corridor.routing.osrm_client import OSRMError, Route, route


def _mock_response(payload, status_ok=True):
    resp = MagicMock()
    resp.json.return_value = payload
    if status_ok:
        resp.raise_for_status.return_value = None
    return resp


def test_route_flips_coordinates_and_parses():
    session = MagicMock()
    session.get.return_value = _mock_response(
        {
            "code": "Ok",
            "routes": [
                {
                    "distance": 500.0,
                    "duration": 120.0,
                    "geometry": {"coordinates": [[-73.9561, 40.6946], [-73.9558, 40.6934]]},
                }
            ],
        }
    )

    r = route(40.6946, -73.9561, 40.6934, -73.9558, base_url="http://localhost:5000", session=session)

    assert r.distance_m == 500.0
    assert r.geometry[0] == (40.6946, -73.9561)  # (lat, lng), flipped from OSRM's (lng, lat)


def test_route_raises_on_bad_code():
    session = MagicMock()
    session.get.return_value = _mock_response({"code": "NoRoute", "message": "no route found"})

    with pytest.raises(OSRMError, match="NoRoute"):
        route(40.6946, -73.9561, 40.6934, -73.9558, base_url="http://localhost:5000", session=session)


def test_route_raises_helpful_error_on_connection_failure():
    import requests

    session = MagicMock()
    session.get.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(OSRMError, match="Could not reach OSRM"):
        route(40.6946, -73.9561, 40.6934, -73.9558, base_url="http://localhost:5000", session=session)


def test_cache_miss_then_hit(tmp_path):
    cache = RouteCache(tmp_path / "routes.sqlite")
    assert cache.get("bike", "5001", "5002") is None

    r = Route(distance_m=500.0, duration_s=120.0, geometry=[(40.69, -73.95), (40.70, -73.96)])
    cache.put("bike", "5001", "5002", r)

    cached = cache.get("bike", "5001", "5002")
    assert cached == r
    cache.close()


def test_get_or_fetch_calls_fetch_fn_only_once(tmp_path):
    cache = RouteCache(tmp_path / "routes.sqlite")
    fetch_fn = MagicMock(
        return_value=Route(distance_m=1.0, duration_s=1.0, geometry=[(0.0, 0.0)])
    )

    cache.get_or_fetch("bike", "5001", "5002", fetch_fn)
    cache.get_or_fetch("bike", "5001", "5002", fetch_fn)

    fetch_fn.assert_called_once()
    cache.close()
