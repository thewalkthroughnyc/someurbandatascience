"""Small-count confidence intervals — STUBBED.

Counts here are small (tens of injuries per block per period) — a bare
percentage change ("injuries doubled from 2 to 4!") is not acceptable
output. This needs a proper small-count interval (e.g. exact Poisson /
Byar's approximation / bootstrap — your call), left for you to implement.
See tests/test_interval.py for the behavior it needs to satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    rate: float | None
    low: float | None
    high: float | None
    is_null: bool
    method: str


def small_count_interval(
    count: int,
    exposure: float,
    method: str = "poisson-exact",
) -> Interval:
    """Confidence interval for a rate (count / exposure) from a small
    Poisson count.

    `is_null` must be set True whenever the interval is uninformative enough
    that reporting a point estimate would mislead — e.g. count=0, or an
    interval so wide it spans an order of magnitude. The front end trusts
    this flag to decide whether to show a number or "not enough data."
    Never let a caller round `is_null=True` data into a displayed rate.
    """
    raise NotImplementedError("small_count_interval is a stub — see METHODS.md")
