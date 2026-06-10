"""Calibration page: synthetic pipeline results against the real aggregated bilan.

This is the "known ground truth" claim made visible. The real values are the
official IR proportions published by the production pipeline (eligible
excluding Voiron denominator, source-censored); the synthetic warehouse is
calibrated on the shipped count layer, so trajectories match closely but not
to the unit.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ...reference import annual_gynecology_real_ir, quarterly_real_ir
from ...registry import INDICATORS, SPECIALTY_LABELS, by_key
from .. import data, theme

_QUARTERLY_SPECS = ("orthopedics", "cardiology")


def _comparison_figure(
    indicator_key: str,
    synthetic: pd.DataFrame,
    real: pd.DataFrame,
    periods: list[str],
) -> go.Figure:
    fig = go.Figure()
    for spec in _QUARTERLY_SPECS:
        color = theme.SPECIALTY_COLORS[spec]
        synth = synthetic[
            (synthetic["indicator"] == indicator_key) & (synthetic["specialty"] == spec)
        ].set_index("period")["proportion"]
        real_s = real[
            (real["indicator"] == indicator_key) & (real["specialty"] == spec)
        ].set_index("period")["proportion"]
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=[synth.get(p) for p in periods],
                mode="lines+markers",
                name=f"{SPECIALTY_LABELS[spec]} · synthetic",
                line={"color": color, "width": 3},
                marker={"size": 7},
                connectgaps=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=[real_s.get(p) for p in periods],
                mode="lines+markers",
                name=f"{SPECIALTY_LABELS[spec]} · real bilan",
                line={"color": color, "width": 2, "dash": "dot"},
                marker={"size": 9, "symbol": "diamond-open"},
                connectgaps=False,
            )
        )
    fig.update_yaxes(tickformat=".0%", range=[-0.02, 1.05])
    fig.update_layout(height=380)
    return theme.style_panel_figure(fig)


def _gap_table(synthetic: pd.DataFrame, real: pd.DataFrame) -> pd.DataFrame:
    merged = real.merge(
        synthetic[["indicator", "specialty", "period", "proportion"]],
        on=["indicator", "specialty", "period"],
        suffixes=("_real", "_synthetic"),
        how="left",
    ).dropna(subset=["proportion_real"])
    merged["gap"] = (merged["proportion_synthetic"] - merged["proportion_real"]).abs()
    rows = []
    for key, group in merged.groupby("indicator"):
        rows.append(
            {
                "indicator": key,
                "points compared": int(group["gap"].notna().sum()),
                "mean abs. gap": group["gap"].mean(),
                "max abs. gap": group["gap"].max(),
            }
        )
    return pd.DataFrame(rows)


def render() -> None:
    """Render the real-versus-synthetic calibration page."""
    theme.banner(
        "Calibration · real vs synthetic",
        "The synthetic warehouse is calibrated on the real, aggregated If-PBM "
        "bilan. Diamonds: official published values. Lines: this pipeline.",
    )
    path = str(data.db_path())
    synthetic = data.load_results(path)
    periods = data.load_periods(path)
    real = quarterly_real_ir()

    tabs = st.tabs([ind.key for ind in INDICATORS])
    for tab, indicator in zip(tabs, INDICATORS, strict=True):
        with tab, st.container(key=f"panel-calib-{indicator.key}"):
            st.markdown(f"#### {indicator.key} · {by_key(indicator.key).title}")
            fig = _comparison_figure(indicator.key, synthetic, real, periods)
            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )

    st.markdown("")
    left, right = st.columns([1.2, 1])
    with left, st.container(key="card-gaps"):
        st.markdown("#### Synthetic-to-real gap (orthopedics + cardiology)")
        gaps = _gap_table(synthetic, real)
        st.dataframe(
            gaps.style.format({"mean abs. gap": "{:.1%}", "max abs. gap": "{:.1%}"}),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Gaps are expected: the official denominator (eligible excluding "
            "Voiron) is not recomputable from the shipped, censored count layer."
        )
    with right, st.container(key="card-gyneco"):
        st.markdown("#### Gynecology: one-year real bilan")
        annual = annual_gynecology_real_ir().pivot(
            index="indicator", columns="specialty", values="proportion"
        )
        annual.columns = [
            str(c).replace("gynecology_", "").capitalize() for c in annual.columns
        ]
        st.dataframe(
            annual.style.format("{:.1%}", na_rep="censored"),
            use_container_width=True,
        )
        st.caption(
            "Gynecology volumes are too small for quarterly reporting; the real "
            "bilan only publishes a one-year value split by procedure. The "
            "synthetic warehouse models a single 'gynecology' specialty, so no "
            "direct comparison is drawn."
        )
