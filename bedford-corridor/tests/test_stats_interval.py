"""stats.interval.small_count_interval is a STUB (see
src/bedford_corridor/stats/interval.py). These tests fail until
implemented — expected.
"""

import pytest

from bedford_corridor.stats.interval import Interval, small_count_interval


def test_small_count_interval_is_currently_a_stub():
    with pytest.raises(NotImplementedError):
        small_count_interval(count=2, exposure=500)


def test_returns_interval_dataclass():
    result = small_count_interval(count=2, exposure=500)
    assert isinstance(result, Interval)


def test_zero_count_is_flagged_null_not_zero_percent():
    result = small_count_interval(count=0, exposure=1000)
    assert result.is_null is True


def test_small_count_never_reported_without_null_flag_when_uninformative():
    # The project brief's explicit requirement: a statistically null/
    # uninformative small-count result must be reported as null, not
    # rounded into a percentage that reads like a finding.
    result = small_count_interval(count=1, exposure=2000)
    if result.is_null:
        assert result.rate is None or result.low is None
    else:
        # if implementation decides 1 count IS informative enough, it must
        # justify that with a bounded interval, not a bare rate
        assert result.low is not None and result.high is not None
