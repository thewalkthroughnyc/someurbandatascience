from unittest.mock import MagicMock

from bedford_corridor.ingest.socrata import fetch_dataset


def _mock_response(rows):
    resp = MagicMock()
    resp.json.return_value = rows
    resp.raise_for_status.return_value = None
    return resp


def test_fetch_dataset_single_page():
    session = MagicMock()
    session.get.return_value = _mock_response([{"a": "1"}, {"a": "2"}])

    df = fetch_dataset("data.cityofnewyork.us", "h9gi-nx95", session=session, page_size=50_000)

    assert len(df) == 2
    session.get.assert_called_once()


def test_fetch_dataset_pages_until_short_page():
    session = MagicMock()
    full_page = [{"a": str(i)} for i in range(3)]
    short_page = [{"a": "x"}]
    session.get.side_effect = [_mock_response(full_page), _mock_response(short_page)]

    df = fetch_dataset("data.cityofnewyork.us", "h9gi-nx95", session=session, page_size=3)

    assert len(df) == 4
    assert session.get.call_count == 2


def test_fetch_dataset_empty_result():
    session = MagicMock()
    session.get.return_value = _mock_response([])

    df = fetch_dataset("data.cityofnewyork.us", "h9gi-nx95", session=session)

    assert df.empty


def test_fetch_dataset_passes_where_and_select():
    session = MagicMock()
    session.get.return_value = _mock_response([])

    fetch_dataset(
        "data.cityofnewyork.us",
        "h9gi-nx95",
        where="crash_date > '2024-01-01'",
        select="collision_id,crash_date",
        session=session,
    )

    _, kwargs = session.get.call_args
    assert kwargs["params"]["$where"] == "crash_date > '2024-01-01'"
    assert kwargs["params"]["$select"] == "collision_id,crash_date"
