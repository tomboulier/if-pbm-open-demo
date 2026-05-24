"""Orchestration: build the demo database (canonical tables + indicator mart).

Mirrors the production ETL direction: generate patient-level data -> load the canonical
schema -> aggregate into the ``indicator_results`` mart.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from .generate import generate, period_dimension
from .indicators import compute_indicators
from .schema import CANONICAL_SCHEMA_SQL, CANONICAL_TABLES, PERIOD_SCHEMA_SQL

DEFAULT_DB_PATH = Path("data/if_pbm.duckdb")


def generate_database(db_path: Path = DEFAULT_DB_PATH, seed: int = 42) -> Path:
    """Generate synthetic canonical data and load it into a fresh DuckDB database.

    Parameters
    ----------
    db_path:
        Where to write the DuckDB file. Overwritten if it exists.
    seed:
        Seed forwarded to the generator.

    Returns
    -------
    pathlib.Path
        The path to the written database.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)

    tables = generate(seed)
    con = duckdb.connect(str(db_path))
    try:
        con.execute(CANONICAL_SCHEMA_SQL)
        con.execute(PERIOD_SCHEMA_SQL)
        loadable = {**tables, "period": period_dimension()}
        for name in (*CANONICAL_TABLES, "period"):
            con.register("frame", loadable[name])
            con.execute(f"INSERT INTO {name} SELECT * FROM frame")
            con.unregister("frame")
    finally:
        con.close()
    return db_path


def compute(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Recompute the indicator mart from the canonical tables in ``db_path``."""
    con = duckdb.connect(str(db_path))
    try:
        compute_indicators(con)
    finally:
        con.close()


def build(db_path: Path = DEFAULT_DB_PATH, seed: int = 42) -> Path:
    """Generate data and compute indicators in one step."""
    generate_database(db_path, seed)
    compute(db_path)
    return db_path
