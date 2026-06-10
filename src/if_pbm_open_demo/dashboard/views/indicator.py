"""Per-indicator drill-down pages, generated from the registry."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import streamlit as st

from ...registry import SPECIALTIES, SPECIALTY_LABELS, Indicator
from .. import components, data, theme


def _definition_card(indicator: Indicator) -> None:
    with st.container(key=f"card-def-{indicator.key}"):
        st.markdown("#### Definition")
        st.markdown(indicator.definition)
        st.markdown(
            f"- **Numerator**: {indicator.numerator}\n"
            f"- **Denominator**: {indicator.denominator}"
        )
        cmp = "≥" if indicator.direction == "higher_is_better" else "≤"
        targets = ", ".join(
            f"{SPECIALTY_LABELS[s]} {cmp}{t:.0%}"
            for s, t in indicator.targets.items()
            if t is not None
        )
        st.markdown(f"- **Year-2 target**: {targets}")
        if indicator.target_note:
            st.caption(indicator.target_note)
        st.caption(
            "Official If-PBM criterion: reach the target OR improve by a set "
            "margin versus baseline; values shown against the year-2 target."
        )


def _kpi_header(indicator: Indicator, results: pd.DataFrame, latest: str) -> None:
    latest_rows = results[
        (results["indicator"] == indicator.key) & (results["period"] == latest)
    ].set_index("specialty")
    columns = st.columns(len(SPECIALTIES))
    for col, spec in zip(columns, SPECIALTIES, strict=True):
        prop = latest_rows["proportion"].get(spec)
        prop = None if prop is None or pd.isna(prop) else float(prop)
        status = indicator.status(prop, spec)
        with col:
            st.markdown(
                components.kpi_disc_html(
                    indicator, prop, status, sub=SPECIALTY_LABELS[spec]
                ),
                unsafe_allow_html=True,
            )


def make_page(indicator: Indicator) -> Callable[[], None]:
    """Build the render function for one indicator page."""

    def render() -> None:
        theme.banner(
            f"{indicator.icon} {indicator.key} · {indicator.title}",
            indicator.definition,
        )
        path = str(data.db_path())
        results = data.load_results(path)
        periods = data.load_periods(path)

        specialties = st.multiselect(
            "Specialties",
            options=list(SPECIALTIES),
            default=list(SPECIALTIES),
            format_func=lambda s: SPECIALTY_LABELS[s],
            key=f"specialties_{indicator.key}",
        )
        if not specialties:
            st.info("Select at least one specialty.")
            return

        latest = periods[-1]
        _kpi_header(indicator, results, latest)
        st.markdown("")

        with st.container(key=f"panel-trend-page-{indicator.key}"):
            st.markdown("#### Trend by trimester, with year-2 targets")
            fig = components.trend_figure(indicator, results, periods, specialties)
            fig.update_layout(height=380)
            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )

        chart_col, def_col = st.columns([1.4, 1])
        with chart_col, st.container(key=f"panel-latest-{indicator.key}"):
            st.markdown(f"#### Latest period ({latest}) by specialty")
            bar = components.latest_bar_figure(indicator, results, latest, specialties)
            bar.update_layout(height=300)
            st.plotly_chart(
                bar, use_container_width=True, config={"displayModeBar": False}
            )
        with def_col:
            _definition_card(indicator)

        with st.expander("Underlying counts"):
            sub = results[
                (results["indicator"] == indicator.key)
                & (results["specialty"].isin(specialties))
            ]
            st.dataframe(
                sub[["specialty", "period", "numerator", "denominator", "proportion"]],
                use_container_width=True,
                hide_index=True,
            )

    render.__name__ = f"indicator_{indicator.key.lower()}"
    return render
