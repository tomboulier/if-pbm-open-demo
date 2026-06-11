"""Cached data access for the platform.

BI pages read only the ``indicator_results`` mart (the output port). The
explorer and training pages intentionally read the canonical tables: the
synthetic warehouse is their teaching surface.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

#: Canonical tables exposed to the explorer / training pages.
EXPLORABLE_TABLES = (
    "patient",
    "surgery",
    "consultation",
    "lab",
    "transfusion",
    "period",
)


def db_path() -> Path:
    """The DuckDB database the platform reads (env-overridable)."""
    return Path(os.environ.get("IF_PBM_DB", "data/if_pbm.duckdb"))


def _connect(path: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(path, read_only=True)


@st.cache_data
def load_results(path: str) -> pd.DataFrame:
    """The indicator mart, ordered for display."""
    con = _connect(path)
    try:
        return con.execute(
            "SELECT indicator, specialty, period, numerator, denominator, proportion "
            "FROM indicator_results ORDER BY indicator, specialty, period"
        ).df()
    finally:
        con.close()


@st.cache_data
def load_periods(path: str) -> list[str]:
    """Period labels in chronological order."""
    con = _connect(path)
    try:
        rows = con.execute("SELECT period FROM period ORDER BY start_date").fetchall()
    finally:
        con.close()
    return [str(r[0]) for r in rows]


@st.cache_data
def load_cohort(path: str) -> pd.DataFrame:
    """Cohort summary: surgeries and patients per specialty."""
    con = _connect(path)
    try:
        return con.execute(
            "SELECT specialty, count(*) AS surgeries, "
            "count(DISTINCT patient_id) AS patients "
            "FROM surgery GROUP BY specialty ORDER BY surgeries DESC"
        ).df()
    finally:
        con.close()


@st.cache_data
def table_preview(path: str, table: str, limit: int = 50) -> pd.DataFrame:
    """First rows of one canonical table (explorer page)."""
    if table not in EXPLORABLE_TABLES:
        raise ValueError(f"not an explorable table: {table!r}")
    con = _connect(path)
    try:
        return con.execute(f"SELECT * FROM {table} LIMIT {int(limit)}").df()
    finally:
        con.close()


@st.cache_data
def table_counts(path: str) -> pd.DataFrame:
    """Row counts of the canonical tables (explorer page)."""
    con = _connect(path)
    try:
        parts = [
            f"SELECT '{t}' AS table_name, count(*) AS rows_ FROM {t}"
            for t in EXPLORABLE_TABLES
        ]
        return con.execute(" UNION ALL ".join(parts)).df()
    finally:
        con.close()


def run_user_query(path: str, sql: str) -> pd.DataFrame:
    """Run an arbitrary read-only query (SQL playground / exercises).

    The connection is read-only, so mutating statements fail naturally; no
    caching, learners expect fresh feedback on every run.
    """
    con = _connect(path)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


def pooled_by_period(results: pd.DataFrame, indicator: str) -> pd.DataFrame:
    """Pooled proportion across specialties, per period, for one indicator."""
    sub = results[results["indicator"] == indicator]
    grouped = sub.groupby("period", as_index=False)[["numerator", "denominator"]].sum()
    grouped["proportion"] = grouped["numerator"] / grouped["denominator"]
    return grouped.sort_values("period")
