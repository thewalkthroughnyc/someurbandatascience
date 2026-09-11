"""stats.did.estimate_did is a STUB (see src/bedford_corridor/stats/did.py).
These tests fail until implemented — expected.
"""

import datetime

import pandas as pd
import pytest

from bedford_corridor.stats.did import DiDResult, estimate_did

TREATMENT_DATE = datetime.date(2025, 8, 6)


def _flat_outcomes():
    # Treated and control blocks move identically before/after — a
    # correctly-implemented estimator must find ~no effect here.
    rows = []
    for block_id, group in [("t1", "treated"), ("t2", "treated"), ("c1", "control"), ("c2", "control")]:
        for period, count in [("2025-06-01", 1), ("2025-07-01", 1), ("2025-09-01", 1), ("2025-10-01", 1)]:
            rows.append({"block_id": block_id, "group": group, "period_date": period, "injury_count": count, "exposure": 1000})
    return pd.DataFrame(rows)


def test_estimate_did_is_currently_a_stub():
    with pytest.raises(NotImplementedError):
        estimate_did(_flat_outcomes(), ["t1", "t2"], ["c1", "c2"], TREATMENT_DATE)


def test_estimate_did_returns_did_result_with_null_flag():
    result = estimate_did(_flat_outcomes(), ["t1", "t2"], ["c1", "c2"], TREATMENT_DATE)
    assert isinstance(result, DiDResult)
    assert isinstance(result.is_null, bool)


def test_estimate_did_flags_null_when_treated_and_control_move_identically():
    # This is the core requirement from the project brief: a null result
    # must come back explicitly labeled null, not rounded into a story.
    result = estimate_did(_flat_outcomes(), ["t1", "t2"], ["c1", "c2"], TREATMENT_DATE)
    assert result.is_null is True
