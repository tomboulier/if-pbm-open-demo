"""Real aggregated If-PBM reference values, shipped with the package.

``real_ir.csv`` carries the official IR proportions published in the If-PBM
bilan (CHU Grenoble Alpes, May 2023 - January 2025): the real-world ground
truth the synthetic pipeline is calibrated against. Aggregated and GDPR-safe:

- computed upstream with the official "eligible excluding Voiron" denominator,
  which the shipped count layer cannot reproduce exactly;
- small-count censoring (``<6``) applied at the source (empty proportions);
- orthopedics / cardiology quarterly; gynecology only as a one-year bilan
  (period ``1Y``), split hysterectomy / ovariectomy.
"""

from __future__ import annotations

from importlib import resources
from io import StringIO

import pandas as pd

#: Period label of the one-year gynecology bilan rows.
ANNUAL_PERIOD = "1Y"


def load_real_ir() -> pd.DataFrame:
    """Load the real aggregated IR reference values.

    Returns
    -------
    pandas.DataFrame
        Columns ``indicator``, ``specialty``, ``period``, ``proportion``
        (NaN where censored at the source).
    """
    text = (
        resources.files(f"{__package__}.data")
        .joinpath("real_ir.csv")
        .read_text("utf-8")
    )
    return pd.read_csv(StringIO(text), dtype={"proportion": float})


def quarterly_real_ir() -> pd.DataFrame:
    """The quarterly (orthopedics / cardiology) slice of the reference."""
    df = load_real_ir()
    return df[df["period"] != ANNUAL_PERIOD].reset_index(drop=True)


def annual_gynecology_real_ir() -> pd.DataFrame:
    """The one-year gynecology slice (hysterectomy / ovariectomy)."""
    df = load_real_ir()
    return df[df["period"] == ANNUAL_PERIOD].reset_index(drop=True)
