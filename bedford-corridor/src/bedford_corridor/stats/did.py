"""Difference-in-differences estimator — STUBBED.

This is the causal core of the analysis (treated = deprotected blocks,
control = still-protected blocks, before/after = TREATMENT_DATE) and is
intentionally left for you to implement, not scaffolded further than the
signature and result shape below. See tests/test_did.py for the behavior
it needs to satisfy — in particular that a null result comes back
labeled null, not rounded into a headline number.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DiDResult:
    estimate: float | None
    ci_low: float | None
    ci_high: float | None
    is_null: bool
    n_treated_blocks: int
    n_control_blocks: int
    n_before_periods: int
    n_after_periods: int
    notes: str = ""


def estimate_did(
    outcomes: pd.DataFrame,
    treated_blocks: list[str],
    control_blocks: list[str],
    treatment_date: datetime.date,
) -> DiDResult:
    """Estimate the treatment effect of protection removal on cyclist
    injuries per block, treated vs. control, before vs. after
    `treatment_date`.

    Parameters
    ----------
    outcomes : one row per (block_id, period_date, injury_count, exposure)
        — exposure here means whatever denominator.trips_per_block()
        produced, joined in upstream.
    treated_blocks, control_blocks : block_id lists.
    treatment_date : the single cutover date (config.corridor.TREATMENT_DATE).

    Returns
    -------
    DiDResult. `is_null` MUST be True whenever the estimated effect's
    confidence interval contains zero (or whatever null-result criterion
    you settle on) — is_null is a required field precisely so the front end
    can render "no detectable effect" instead of a bare point estimate that
    reads as a finding when it isn't one.
    """
    raise NotImplementedError("estimate_did is a stub — see METHODS.md")
