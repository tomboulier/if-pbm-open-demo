"""Overview page: cohort header, KPI discs, small-multiple trends."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ...registry import INDICATORS, SPECIALTIES, SPECIALTY_LABELS
from .. import components, data, theme


def _cohort_card(cohort: pd.DataFrame) -> None:
    with st.container(key="card-cohort"):
        st.markdown("#### Cohort")
        total_surgeries = int(cohort["surgeries"].sum())
        st.metric("Surgeries", f"{total_surgeries:,}")
        donut = go.Figure(
            go.Pie(
                labels=[SPECIALTY_LABELS.get(s, s) for s in cohort["specialty"]],
                values=cohort["surgeries"],
                hole=0.55,
                marker={
                    "colors": [
                        theme.SPECIALTY_COLORS.get(s, theme.NO_DATA)
                        for s in cohort["specialty"]
                    ]
                },
                textinfo="percent",
            )
        )
        donut.update_layout(
            showlegend=True,
            height=190,
            legend={"orientation": "h", "y": -0.15, "x": 0},
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
        )
        theme.style_card_figure(donut)
        st.plotly_chart(
            donut, use_container_width=True, config={"displayModeBar": False}
        )
        st.caption(
            "Synthetic cohort calibrated on the real bilan; the generator "
            "draws one synthetic patient per surgery."
        )


def _kpi_row(results: pd.DataFrame, periods: list[str]) -> None:
    latest = periods[-1]
    columns = st.columns(len(INDICATORS))
    for col, indicator in zip(columns, INDICATORS, strict=True):
        pooled = data.pooled_by_period(results, indicator.key).set_index("period")
        value = pooled["proportion"].get(latest)
        value = None if value is None or pd.isna(value) else float(value)
        latest_rows = results[
            (results["indicator"] == indicator.key) & (results["period"] == latest)
        ].set_index("specialty")
        statuses = []
        for spec in SPECIALTIES:
            prop = latest_rows["proportion"].get(spec)
            prop = None if prop is None or pd.isna(prop) else float(prop)
            statuses.append(indicator.status(prop, spec))
        overall = (
            "met"
            if all(s in ("met", "no_target") for s in statuses)
            and any(s == "met" for s in statuses)
            else "missed"
            if any(s == "missed" for s in statuses)
            else "no_data"
        )
        with col:
            st.markdown(
                components.kpi_disc_html(
                    indicator, value, overall, sub=indicator.short_label
                ),
                unsafe_allow_html=True,
            )
            chips = "".join(
                components.status_chip_html(SPECIALTY_LABELS[s][:1], status)
                for s, status in zip(SPECIALTIES, statuses, strict=True)
            )
            st.markdown(
                f'<div style="text-align:center">{chips}</div>',
                unsafe_allow_html=True,
            )
            page_refs = st.session_state.get("page_refs", {})
            if indicator.key in page_refs:
                st.page_link(
                    page_refs[indicator.key],
                    label=f"Open {indicator.key}",
                    use_container_width=True,
                )


def _trend_grid(results: pd.DataFrame, periods: list[str]) -> None:
    specialties = list(SPECIALTIES)
    rows = (INDICATORS[:3], INDICATORS[3:])
    for group in rows:
        columns = st.columns(3)
        for col, indicator in zip(columns, group, strict=False):
            with col, st.container(key=f"panel-trend-{indicator.key}"):
                st.markdown(f"#### {indicator.key} · {indicator.title}")
                fig = components.trend_figure(indicator, results, periods, specialties)
                fig.update_layout(height=260, showlegend=False)
                st.plotly_chart(
                    fig, use_container_width=True, config={"displayModeBar": False}
                )


def render() -> None:
    """Render the overview page."""
    theme.banner(
        "If-PBM · PBM guideline adherence",
        "Synthetic clinical data warehouse calibrated on the real, aggregated "
        "If-PBM bilan (CHU Grenoble Alpes, 2023-2025). Latest period at a glance.",
    )
    path = str(data.db_path())
    results = data.load_results(path)
    periods = data.load_periods(path)

    left, right = st.columns([1, 2.4])
    with left:
        _cohort_card(data.load_cohort(path))
    with right:
        with st.container(key="card-kpis"):
            st.markdown(f"#### Latest period: **{periods[-1]}**")
            _kpi_row(results, periods)

    st.markdown("")
    _trend_grid(results, periods)
