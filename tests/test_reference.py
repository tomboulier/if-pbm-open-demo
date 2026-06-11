"""The shipped real aggregated reference matches the published bilan."""

import math

import pytest

from if_pbm_open_demo.reference import (
    annual_gynecology_real_ir,
    load_real_ir,
    quarterly_real_ir,
)
from if_pbm_open_demo.registry import INDICATORS


def test_reference_covers_every_indicator() -> None:
    df = load_real_ir()
    assert set(df["indicator"]) == {ind.key for ind in INDICATORS}


def test_quarterly_slice_is_ortho_cardio_over_seven_quarters() -> None:
    df = quarterly_real_ir()
    assert set(df["specialty"]) == {"orthopedics", "cardiology"}
    counts = df.groupby(["indicator", "specialty"]).size()
    assert (counts == 7).all()


def test_annual_slice_is_the_one_year_gynecology_bilan() -> None:
    df = annual_gynecology_real_ir()
    assert set(df["specialty"]) == {
        "gynecology_hysterectomy",
        "gynecology_ovariectomy",
    }
    assert len(df) == 10  # 5 indicators x 2 procedures


def test_proportions_are_within_unit_interval_or_censored() -> None:
    values = load_real_ir()["proportion"]
    valid = values.dropna()
    assert ((valid >= 0) & (valid <= 1)).all()
    assert values.isna().sum() > 0  # source censoring must be preserved


@pytest.mark.parametrize(
    ("indicator", "specialty", "period", "expected"),
    [
        # IR4 ortho Aug 2023 = 12 / (170 - 45): the official 'excluding Voiron'
        # denominator, not recomputable from the count layer.
        ("IR4", "orthopedics", "2023-T2", 0.096),
        # IR2 ortho Aug 2024 = 3/17: the '3' is censored in the count layer but
        # the upstream pipeline published the ratio.
        ("IR2", "orthopedics", "2024-T3", 0.176471),
        ("IR1", "cardiology", "2023-T1", 0.594595),
    ],
)
def test_sentinel_values_match_the_published_bilan(
    indicator: str, specialty: str, period: str, expected: float
) -> None:
    df = load_real_ir()
    row = df[
        (df["indicator"] == indicator)
        & (df["specialty"] == specialty)
        & (df["period"] == period)
    ]
    assert len(row) == 1
    assert math.isclose(row["proportion"].iloc[0], expected, abs_tol=1e-6)
