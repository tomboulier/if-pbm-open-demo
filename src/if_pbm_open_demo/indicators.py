"""Compute IR1-IR5 over the canonical schema and materialise the results mart.

Each indicator is a small SQL query (in ``sql/``) returning ``specialty``, ``period``,
``numerator`` and ``denominator``. This module wraps each query to add the indicator
label and the proportion, then inserts the rows into the ``indicator_results`` mart,
the sole contract consumed by any dashboard.
"""

from __future__ import annotations

from importlib import resources

import duckdb

from .schema import LOW_HB_THRESHOLD_G_DL, MART_SCHEMA_SQL

#: Indicator label -> SQL file name.
INDICATORS: dict[str, str] = {
    "IR1": "ir1.sql",
    "IR2": "ir2.sql",
    "IR3": "ir3.sql",
    "IR4": "ir4.sql",
    "IR5": "ir5.sql",
}


def _load_sql(name: str) -> str:
    return (
        resources.files(f"{__package__}.sql").joinpath(name).read_text(encoding="utf-8")
    )


def compute_indicators(con: duckdb.DuckDBPyConnection) -> None:
    """Compute every indicator and (re)build the ``indicator_results`` mart.

    Parameters
    ----------
    con:
        A DuckDB connection whose database already contains the canonical tables.
    """
    con.execute("DROP TABLE IF EXISTS indicator_results")
    con.execute(MART_SCHEMA_SQL)

    for label, sql_file in INDICATORS.items():
        base_query = _load_sql(sql_file)
        wrapped = f"""
            INSERT INTO indicator_results
            SELECT
                '{label}' AS indicator,
                specialty,
                period,
                numerator,
                denominator,
                CASE WHEN denominator = 0 THEN NULL
                     ELSE numerator::DOUBLE / denominator END AS proportion
            FROM ({base_query})
        """
        params = {"low_hb": LOW_HB_THRESHOLD_G_DL} if "$low_hb" in base_query else {}
        con.execute(wrapped, params)
