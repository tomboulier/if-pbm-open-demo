"""Streamlit dashboard: one output adapter, reading only the indicator mart.

Two levels: an at-a-glance overview (KPI tiles + heatmap of the latest period) and a
per-indicator drill-down (trend line, latest-period bar, underlying table). It never
touches the canonical source tables, so swapping it for another BI tool (e.g. Superset
for D2H) needs no change to data generation or indicator computation.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# Short and full labels for each indicator.
INDICATOR_LABELS = {
    "IR1": "Preoperative PBM check-up",
    "IR2": "Anemia / iron correction",
    "IR3": "Single-unit transfusion episodes",
    "IR4": "Transfused per/post-op",
    "IR5": "Low hemoglobin at discharge",
}

# Direction in which an improving indicator moves (drives the KPI delta colour).
GOOD_DIRECTION = {"IR1": "up", "IR2": "up", "IR3": "up", "IR4": "down", "IR5": "down"}


def _db_path() -> Path:
    return Path(os.environ.get("IF_PBM_DB", "data/if_pbm.duckdb"))


@st.cache_data
def load_results(db_path: str) -> pd.DataFrame:
    """Read the indicator results mart (the only table this dashboard depends on)."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        return con.execute(
            "SELECT indicator, specialty, period, numerator, denominator, proportion "
            "FROM indicator_results ORDER BY indicator, specialty, period"
        ).df()
    finally:
        con.close()


def _pooled_by_period(results: pd.DataFrame, indicator: str) -> pd.DataFrame:
    """Pooled proportion across specialties, per period, for one indicator."""
    sub = results[results["indicator"] == indicator]
    grouped = sub.groupby("period", as_index=False)[["numerator", "denominator"]].sum()
    grouped["proportion"] = grouped["numerator"] / grouped["denominator"]
    return grouped.sort_values("period")


def _render_overview(results: pd.DataFrame, periods: list[str]) -> None:
    latest = periods[-1]
    previous = periods[-2] if len(periods) > 1 else None
    st.subheader(f"At a glance - latest period: {latest}")

    columns = st.columns(len(INDICATOR_LABELS))
    for col, (indicator, label) in zip(columns, INDICATOR_LABELS.items(), strict=True):
        pooled = _pooled_by_period(results, indicator).set_index("period")["proportion"]
        value = pooled.get(latest)
        delta = None
        if previous is not None and previous in pooled.index and value is not None:
            delta = f"{(value - pooled[previous]) * 100:+.1f} pts"
        with col:
            st.metric(
                label=f"{indicator}",
                value="-" if value is None else f"{value:.0%}",
                delta=delta,
                delta_color="normal"
                if GOOD_DIRECTION[indicator] == "up"
                else "inverse",
                help=label,
            )
            if st.button(
                "View trends", key=f"btn_{indicator}", use_container_width=True
            ):
                st.session_state["indicator"] = indicator
                st.rerun()

    st.divider()
    st.subheader(f"All indicators by specialty - {latest}")
    snapshot = results[results["period"] == latest].pivot_table(
        index="indicator", columns="specialty", values="proportion"
    )
    fig = px.imshow(
        snapshot,
        text_auto=".0%",
        color_continuous_scale="Blues",
        aspect="auto",
        labels={"color": "proportion"},
    )
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(fig, use_container_width=True)


def _render_trends(results: pd.DataFrame, indicator: str, periods: list[str]) -> None:
    if st.button("← Back to overview"):
        st.session_state["indicator"] = None
        st.rerun()

    st.subheader(f"{indicator} - {INDICATOR_LABELS[indicator]}")
    sub = results[results["indicator"] == indicator]

    line = px.line(sub, x="period", y="proportion", color="specialty", markers=True)
    line.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 1], xaxis_title="")
    line.update_layout(title="Trend over periods")
    st.plotly_chart(line, use_container_width=True)

    latest = periods[-1]
    bar = px.bar(
        sub[sub["period"] == latest],
        x="specialty",
        y="proportion",
        color="specialty",
        text_auto=".0%",
    )
    bar.update_layout(
        yaxis_tickformat=".0%", yaxis_range=[0, 1], showlegend=False, xaxis_title=""
    )
    bar.update_layout(title=f"Latest period ({latest}) by specialty")
    st.plotly_chart(bar, use_container_width=True)

    with st.expander("Underlying counts"):
        st.dataframe(
            sub[["specialty", "period", "numerator", "denominator", "proportion"]],
            use_container_width=True,
            hide_index=True,
        )


def main() -> None:
    """Render the overview or the trend drill-down for a chosen indicator."""
    st.set_page_config(page_title="If-PBM Open Demo", layout="wide")
    st.title("If-PBM - PBM guideline adherence")
    st.caption(
        "Synthetic data calibrated to the aggregated If-PBM bilan. "
        "Reproducibility demo of the MIE2026 method "
        "(Grenoble Alpes University Hospital)."
    )

    db = _db_path()
    if not db.exists():
        st.warning(f"No database at {db}. Run `if-pbm-demo demo` first.")
        return

    results = load_results(str(db))
    periods = sorted(results["period"].unique())
    indicator = st.session_state.get("indicator")
    if indicator is None:
        _render_overview(results, periods)
    else:
        _render_trends(results, indicator, periods)


if __name__ == "__main__":
    main()
