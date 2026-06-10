"""Visual identity of the platform, after the validated dashboard mockups.

Cream page, blue-grey rounded panels with white text, KPI discs coloured by
target status. Everything colour-related lives here so pages and components
stay declarative.
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st

# Page & panels -------------------------------------------------------------
CREAM = "#F2EFE6"
PANEL = "#5E89A6"
PANEL_DARK = "#49718C"
CARD = "#FBFAF5"
NAVY = "#1C3D5C"
TEXT_MUTED = "#5E6B76"

# Series --------------------------------------------------------------------
ORTHO = "#1F4E79"
CARDIO = "#E8536F"
GYNECO = "#9C8ADE"
POOLED = "#F2EFE6"  # light line on blue panels

SPECIALTY_COLORS = {
    "orthopedics": ORTHO,
    "cardiology": CARDIO,
    "gynecology": GYNECO,
}

# Target status -------------------------------------------------------------
MET = "#A5D86E"
MISSED = "#F4628C"
NO_TARGET = "#F5B942"
NO_DATA = "#B6C2CC"

STATUS_COLORS = {
    "met": MET,
    "missed": MISSED,
    "no_target": NO_TARGET,
    "no_data": NO_DATA,
}

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;600;700&display=swap');

html, body, [class*="stApp"] {{
    font-family: 'Lexend', 'Source Sans Pro', sans-serif;
}}
.stApp {{
    background-color: {CREAM};
}}
[data-testid="stSidebar"] {{
    background-color: {CARD};
    border-right: 1px solid #E3DFD2;
}}
h1, h2, h3 {{
    color: {NAVY};
}}

/* Banner title, as in the mockups */
.pbm-banner {{
    background: {PANEL};
    color: white;
    border-radius: 14px;
    padding: 0.9rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 6px rgba(28, 61, 92, 0.18);
}}
.pbm-banner h1 {{
    color: white;
    font-size: 1.7rem;
    font-weight: 600;
    margin: 0;
}}
.pbm-banner p {{
    color: #DCE7EE;
    margin: 0.15rem 0 0 0;
    font-size: 0.9rem;
}}

/* Blue chart panel */
div[class*="st-key-panel"] {{
    background: {PANEL};
    border-radius: 14px;
    padding: 1.0rem 1.2rem;
    box-shadow: 0 2px 6px rgba(28, 61, 92, 0.18);
}}
div[class*="st-key-panel"] h3,
div[class*="st-key-panel"] h4,
div[class*="st-key-panel"] p,
div[class*="st-key-panel"] span,
div[class*="st-key-panel"] label {{
    color: white !important;
}}

/* Cream cards (cohort, definitions, exercises) */
div[class*="st-key-card"] {{
    background: {CARD};
    border-radius: 14px;
    padding: 1.0rem 1.2rem;
    border: 1px solid #E3DFD2;
}}

/* KPI disc */
.pbm-kpi {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
}}
.pbm-kpi .disc {{
    width: 86px;
    height: 86px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.05rem;
    color: {NAVY};
    border: 4px solid rgba(255, 255, 255, 0.65);
    box-shadow: 0 2px 5px rgba(28, 61, 92, 0.25);
}}
.pbm-kpi .key {{
    font-weight: 700;
    color: {NAVY};
    background: white;
    border-radius: 10px;
    padding: 0.05rem 0.65rem;
    box-shadow: 0 1px 3px rgba(28, 61, 92, 0.18);
}}
.pbm-kpi .sub {{
    font-size: 0.75rem;
    color: {TEXT_MUTED};
}}

/* Status chips */
.pbm-chip {{
    display: inline-block;
    border-radius: 999px;
    padding: 0.05rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: {NAVY};
    margin-right: 0.25rem;
}}
</style>
"""


def inject_theme() -> None:
    """Inject the platform CSS once per rerun."""
    st.markdown(_CSS, unsafe_allow_html=True)


def banner(title: str, subtitle: str) -> None:
    """Render the rounded blue page banner."""
    st.markdown(
        f'<div class="pbm-banner"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def style_panel_figure(fig: go.Figure, **layout: Any) -> go.Figure:
    """Style a plotly figure for display on a blue panel (white text)."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white", "family": "Lexend, sans-serif"},
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        legend={"orientation": "h", "y": 1.12, "x": 0},
        **layout,
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.15)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.2)", zeroline=False)
    return fig


def style_card_figure(fig: go.Figure, **layout: Any) -> go.Figure:
    """Style a plotly figure for display on a cream card (navy text)."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": NAVY, "family": "Lexend, sans-serif"},
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        **layout,
    )
    return fig
