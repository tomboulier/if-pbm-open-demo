"""Reusable visual components derived from the registry (KPI discs, chips,
target decorations). Pure rendering: no data access here."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..registry import SPECIALTY_LABELS, Indicator
from . import theme


def kpi_disc_html(
    indicator: Indicator,
    value: float | None,
    status: str,
    sub: str = "",
) -> str:
    """A mockup-style KPI disc: big %, IR badge, status colour."""
    text = "–" if value is None else f"{value:.1%}"
    color = theme.STATUS_COLORS.get(status, theme.NO_DATA)
    sub_html = f'<span class="sub">{sub}</span>' if sub else ""
    return (
        '<div class="pbm-kpi">'
        f'<div class="disc" style="background:{color}">{text}</div>'
        f'<span class="key">{indicator.icon} {indicator.key}</span>'
        f"{sub_html}"
        "</div>"
    )


def status_chip_html(label: str, status: str) -> str:
    """A small pill showing a per-specialty target status."""
    color = theme.STATUS_COLORS.get(status, theme.NO_DATA)
    mark = {"met": "✓", "missed": "✗"}.get(status, "·")
    return f'<span class="pbm-chip" style="background:{color}">{label} {mark}</span>'


def trend_figure(
    indicator: Indicator,
    results: pd.DataFrame,
    periods: list[str],
    specialties: list[str],
    show_targets: bool = True,
) -> go.Figure:
    """Per-specialty trend lines with year-2 target lines, panel-styled.

    Target lines follow the deck conventions: always labelled in the legend
    with the direction of the threshold, never inline on the chart.
    """
    sub = results[results["indicator"] == indicator.key]
    fig = go.Figure()
    for spec in specialties:
        spec_df = sub[sub["specialty"] == spec].set_index("period")
        y = [spec_df["proportion"].get(p) for p in periods]
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=y,
                mode="lines+markers",
                name=SPECIALTY_LABELS.get(spec, spec),
                line={
                    "color": theme.SPECIALTY_COLORS.get(spec, theme.POOLED),
                    "width": 3,
                },
                marker={"size": 7},
                connectgaps=False,
            )
        )
    if show_targets:
        _add_target_lines(fig, indicator, periods, specialties)
    fig.update_yaxes(tickformat=".0%", range=[-0.02, 1.05])
    return theme.style_panel_figure(fig)


def _add_target_lines(
    fig: go.Figure,
    indicator: Indicator,
    periods: list[str],
    specialties: list[str],
) -> None:
    cmp = "≥" if indicator.direction == "higher_is_better" else "≤"
    shown = {
        indicator.targets[s] for s in specialties if indicator.targets[s] is not None
    }
    shared = len(shown) == 1 and all(
        indicator.targets[s] is not None for s in specialties
    )
    for spec in specialties:
        target = indicator.targets[spec]
        if target is None:
            continue
        label = (
            f"Y2 target {cmp}{target:.0%}"
            if shared
            else f"{SPECIALTY_LABELS[spec]} target {cmp}{target:.0%}"
        )
        color = "rgba(255,255,255,0.85)" if shared else theme.SPECIALTY_COLORS[spec]
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=[target] * len(periods),
                mode="lines",
                name=label,
                line={"color": color, "width": 1.6, "dash": "dash"},
                hoverinfo="skip",
            )
        )
        if shared:
            break


def latest_bar_figure(
    indicator: Indicator,
    results: pd.DataFrame,
    period: str,
    specialties: list[str],
) -> go.Figure:
    """Latest-period bars per specialty, coloured by target status."""
    sub = results[
        (results["indicator"] == indicator.key) & (results["period"] == period)
    ].set_index("specialty")
    labels, values, colors = [], [], []
    for spec in specialties:
        value = sub["proportion"].get(spec)
        prop = None if value is None or pd.isna(value) else float(value)
        labels.append(SPECIALTY_LABELS.get(spec, spec))
        values.append(prop)
        colors.append(theme.STATUS_COLORS[indicator.status(prop, spec)])
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[("–" if v is None else f"{v:.0%}") for v in values],
            textposition="outside",
        )
    )
    fig.update_yaxes(tickformat=".0%", range=[0, 1.08])
    fig.update_layout(showlegend=False)
    return theme.style_panel_figure(fig)
