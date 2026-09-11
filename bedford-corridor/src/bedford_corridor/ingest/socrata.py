"""Thin, paginated SoQL client for Socrata (data.cityofnewyork.us) datasets.

Boilerplate: no analytical logic lives here, just fetch-and-page. An optional
app token (SOCRATA_APP_TOKEN env var) raises the throttling limit but isn't
required for the volumes this project pulls.
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

PAGE_SIZE = 50_000


def fetch_dataset(
    domain: str,
    dataset_id: str,
    where: str | None = None,
    select: str | None = None,
    order: str | None = None,
    page_size: int = PAGE_SIZE,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch a full Socrata dataset (with optional SoQL filters), paging past
    the per-request row cap. Returns all matching rows as a DataFrame of
    strings — callers are responsible for their own dtype coercion, since
    Socrata's JSON typing (e.g. BBL-like ID fields) is not always trustworthy.
    """
    session = session or requests.Session()
    url = f"https://{domain}/resource/{dataset_id}.json"
    headers = {}
    token = os.environ.get("SOCRATA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token

    frames: list[pd.DataFrame] = []
    offset = 0
    while True:
        params: dict[str, Any] = {"$limit": page_size, "$offset": offset}
        if where:
            params["$where"] = where
        if select:
            params["$select"] = select
        if order:
            params["$order"] = order

        resp = session.get(url, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            break

        frames.append(pd.DataFrame(rows))
        if len(rows) < page_size:
            break
        offset += page_size

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
