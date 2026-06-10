"""Self-correcting SQL training track over the synthetic warehouse.

Each exercise pairs a statement with a reference solution; a learner attempt
is validated by running both queries against the same read-only database and
comparing results (column names case-insensitively, row order ignored, float
proportions within tolerance). Because every indicator value of the synthetic
warehouse is known by construction, feedback is exact: this is the
known-ground-truth promise turned into a teaching device.

No Streamlit here: the engine is plain Python so it can be tested and reused.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

#: Absolute tolerance when comparing floating-point columns.
FLOAT_TOLERANCE = 1e-6


@dataclass(frozen=True)
class Exercise:
    """One training exercise with its reference solution."""

    key: str
    level: int
    title: str
    statement: str
    starter_sql: str
    hints: tuple[str, ...]
    solution_sql: str


@dataclass(frozen=True)
class Feedback:
    """Outcome of validating a learner attempt."""

    ok: bool
    message: str
    expected_shape: tuple[int, int] | None = None
    got_shape: tuple[int, int] | None = None


EXERCISES: tuple[Exercise, ...] = (
    Exercise(
        key="cohort",
        level=1,
        title="Size the cohort",
        statement=(
            "How many surgeries does each specialty contribute?\n\n"
            "Return two columns: `specialty` and `n_surgeries`, one row per "
            "specialty."
        ),
        starter_sql="SELECT specialty, count(*) AS n_surgeries\nFROM surgery\n-- ...",
        hints=(
            "Everything you need is in the `surgery` table.",
            "GROUP BY specialty; name the count `n_surgeries`.",
        ),
        solution_sql=(
            "SELECT specialty, count(*) AS n_surgeries FROM surgery GROUP BY specialty"
        ),
    ),
    Exercise(
        key="trimesters",
        level=1,
        title="Join the reporting calendar",
        statement=(
            "If-PBM reports on rolling three-month trimesters that do not match "
            "calendar quarters, so the period is a dimension table joined by "
            "date range.\n\n"
            "Count surgeries per reporting period: return `period` and "
            "`n_surgeries`."
        ),
        starter_sql=(
            "SELECT pd.period, count(*) AS n_surgeries\n"
            "FROM surgery s\n"
            "JOIN period pd ON -- ?\n"
            "GROUP BY pd.period"
        ),
        hints=(
            "Join `surgery.surgery_date` to the period's date range.",
            "`s.surgery_date BETWEEN pd.start_date AND pd.end_date`.",
        ),
        solution_sql=(
            "SELECT pd.period, count(*) AS n_surgeries\n"
            "FROM surgery s\n"
            "JOIN period pd ON s.surgery_date BETWEEN pd.start_date AND pd.end_date\n"
            "GROUP BY pd.period"
        ),
    ),
    Exercise(
        key="ir1",
        level=2,
        title="Recompute IR1 (preoperative check-up)",
        statement=(
            "IR1 is the proportion of standardized PBM check-ups among "
            "surgeries with a pre-anesthesia consultation.\n\n"
            "Recompute its building blocks per specialty and period: return "
            "`specialty`, `period`, `numerator` (check-ups done) and "
            "`denominator` (consultations). Your result must match the official "
            "mart exactly."
        ),
        starter_sql=(
            "SELECT\n"
            "    s.specialty,\n"
            "    pd.period,\n"
            "    -- numerator: consultations with pbm_checkup_done\n"
            "    -- denominator: all consultations\n"
            "FROM surgery s\n"
            "JOIN consultation c ON c.surgery_id = s.surgery_id\n"
            "JOIN period pd ON s.surgery_date BETWEEN pd.start_date AND pd.end_date\n"
            "GROUP BY 1, 2"
        ),
        hints=(
            "`count(*) FILTER (WHERE c.pbm_checkup_done)` counts the numerator.",
            "The denominator is simply `count(*)` after the consultation join.",
        ),
        solution_sql=(
            "SELECT\n"
            "    s.specialty AS specialty,\n"
            "    pd.period AS period,\n"
            "    count(*) FILTER (WHERE c.pbm_checkup_done) AS numerator,\n"
            "    count(*) AS denominator\n"
            "FROM surgery s\n"
            "JOIN consultation c ON c.surgery_id = s.surgery_id\n"
            "JOIN period pd ON s.surgery_date BETWEEN pd.start_date AND pd.end_date\n"
            "GROUP BY 1, 2"
        ),
    ),
    Exercise(
        key="ir4",
        level=2,
        title="Recompute IR4 (transfused patients)",
        statement=(
            "IR4 is the proportion of patients transfused per- or "
            "post-operatively: at least one RBC unit within 30 days of surgery, "
            "among all operated patients.\n\n"
            "Return `specialty`, `period`, `numerator`, `denominator`. Beware: "
            "several units must still count as ONE transfused patient."
        ),
        starter_sql=(
            "-- One row per surgery first, then aggregate.\n"
            "WITH transfused AS (\n"
            "    SELECT s.surgery_id, s.specialty, s.surgery_date,\n"
            "           -- was this surgery transfused within 30 days?\n"
            "    FROM surgery s\n"
            ")\n"
            "SELECT ..."
        ),
        hints=(
            "An EXISTS subquery on `transfusion` avoids double counting.",
            "Filter units: product_type = 'RBC' AND delivery between the "
            "surgery date and surgery date + 30 days.",
            "Compare your totals with the IR4 page before submitting.",
        ),
        solution_sql=(
            "WITH transfused AS (\n"
            "    SELECT s.surgery_id, s.specialty, s.surgery_date,\n"
            "           EXISTS (\n"
            "               SELECT 1 FROM transfusion t\n"
            "               WHERE t.surgery_id = s.surgery_id\n"
            "                 AND t.product_type = 'RBC'\n"
            "                 AND t.delivery_datetime >= s.surgery_date\n"
            "                 AND t.delivery_datetime\n"
            "                     < s.surgery_date + INTERVAL 30 DAY\n"
            "           ) AS was_transfused\n"
            "    FROM surgery s\n"
            ")\n"
            "SELECT tr.specialty AS specialty, pd.period AS period,\n"
            "       count(*) FILTER (WHERE tr.was_transfused) AS numerator,\n"
            "       count(*) AS denominator\n"
            "FROM transfused tr\n"
            "JOIN period pd ON tr.surgery_date BETWEEN pd.start_date AND pd.end_date\n"
            "GROUP BY 1, 2"
        ),
    ),
    Exercise(
        key="ir3",
        level=3,
        title="Recompute IR3 (single-unit episodes)",
        statement=(
            "The hard one. A transfusion *episode* is a run of RBC units less "
            "than one hour apart; IR3 is the proportion of episodes delivering "
            "exactly one unit.\n\n"
            "Return `specialty`, `period`, `numerator` (single-unit episodes) "
            "and `denominator` (all episodes). Units are censored at 30 days "
            "after surgery."
        ),
        starter_sql=(
            "-- Window functions are your friend:\n"
            "-- 1. flag units that OPEN an episode (lag() > 1 hour or first),\n"
            "-- 2. number episodes with a running sum,\n"
            "-- 3. size each episode, then aggregate.\n"
            "WITH rbc AS (\n"
            "    SELECT t.surgery_id, s.specialty, s.surgery_date,\n"
            "           t.delivery_datetime\n"
            "    FROM transfusion t JOIN surgery s ON s.surgery_id = t.surgery_id\n"
            "    WHERE t.product_type = 'RBC'\n"
            "      AND t.delivery_datetime >= s.surgery_date\n"
            "      AND t.delivery_datetime\n"
            "          < s.surgery_date + INTERVAL 30 DAY\n"
            ")\n"
            "SELECT ..."
        ),
        hints=(
            "`lag(delivery_datetime) OVER (PARTITION BY surgery_id ORDER BY "
            "delivery_datetime)` gives the previous unit.",
            "An episode opens when the gap is NULL or greater than 1 hour; a "
            "running `sum()` of that flag numbers the episodes.",
            "Group by (surgery, episode) to size episodes, then count episodes "
            "of size one per specialty and period.",
        ),
        solution_sql=(
            "WITH rbc AS (\n"
            "    SELECT t.surgery_id, s.specialty, s.surgery_date,\n"
            "           t.delivery_datetime\n"
            "    FROM transfusion t JOIN surgery s ON s.surgery_id = t.surgery_id\n"
            "    WHERE t.product_type = 'RBC'\n"
            "      AND t.delivery_datetime >= s.surgery_date\n"
            "      AND t.delivery_datetime\n"
            "          < s.surgery_date + INTERVAL 30 DAY\n"
            "),\n"
            "flagged AS (\n"
            "    SELECT *, CASE WHEN lag(delivery_datetime) OVER w IS NULL\n"
            "                     OR delivery_datetime\n"
            "                        - lag(delivery_datetime) OVER w\n"
            "                        > INTERVAL 1 HOUR\n"
            "              THEN 1 ELSE 0 END AS opens_episode\n"
            "    FROM rbc\n"
            "    WINDOW w AS (PARTITION BY surgery_id ORDER BY delivery_datetime)\n"
            "),\n"
            "episodes AS (\n"
            "    SELECT *, sum(opens_episode) OVER (\n"
            "        PARTITION BY surgery_id ORDER BY delivery_datetime\n"
            "    ) AS episode_no\n"
            "    FROM flagged\n"
            "),\n"
            "episode_sizes AS (\n"
            "    SELECT surgery_id, specialty, surgery_date, episode_no,\n"
            "           count(*) AS n_units\n"
            "    FROM episodes GROUP BY 1, 2, 3, 4\n"
            ")\n"
            "SELECT es.specialty AS specialty, pd.period AS period,\n"
            "       count(*) FILTER (WHERE es.n_units = 1) AS numerator,\n"
            "       count(*) AS denominator\n"
            "FROM episode_sizes es\n"
            "JOIN period pd ON es.surgery_date BETWEEN pd.start_date AND pd.end_date\n"
            "GROUP BY 1, 2"
        ),
    ),
)


def by_key(key: str) -> Exercise:
    """Return the exercise with the given key, or raise ``KeyError``."""
    for exercise in EXERCISES:
        if exercise.key == key:
            return exercise
    raise KeyError(f"unknown exercise: {key!r}")


def _run(db_path: Path, sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase columns, order-insensitive rows, rounded floats."""
    out = df.copy()
    out.columns = [str(c).lower() for c in out.columns]
    out = out.reindex(sorted(out.columns), axis=1)
    for column in out.columns:
        if pd.api.types.is_float_dtype(out[column]):
            out[column] = out[column].round(6)
    return out.sort_values(list(out.columns)).reset_index(drop=True)


def check_attempt(db_path: Path, exercise: Exercise, learner_sql: str) -> Feedback:
    """Validate a learner attempt against the reference solution."""
    expected = _normalize(_run(db_path, exercise.solution_sql))
    try:
        got = _normalize(_run(db_path, learner_sql))
    except Exception as exc:  # noqa: BLE001 - the error IS the feedback
        return Feedback(ok=False, message=f"Your query failed: {exc}")

    if set(got.columns) != set(expected.columns):
        missing = set(expected.columns) - set(got.columns)
        extra = set(got.columns) - set(expected.columns)
        parts = []
        if missing:
            parts.append(f"missing column(s): {', '.join(sorted(missing))}")
        if extra:
            parts.append(f"unexpected column(s): {', '.join(sorted(extra))}")
        return Feedback(
            ok=False,
            message="Column mismatch: " + "; ".join(parts),
            expected_shape=expected.shape,
            got_shape=got.shape,
        )
    if len(got) != len(expected):
        return Feedback(
            ok=False,
            message=(
                f"Row count mismatch: expected {len(expected)} rows, got {len(got)}."
            ),
            expected_shape=expected.shape,
            got_shape=got.shape,
        )
    try:
        pd.testing.assert_frame_equal(
            got, expected, check_dtype=False, atol=FLOAT_TOLERANCE
        )
    except AssertionError:
        diff_mask = (got != expected) & ~(got.isna() & expected.isna())
        n_bad = int(diff_mask.any(axis=1).sum())
        return Feedback(
            ok=False,
            message=(
                f"Shape is right but {n_bad} row(s) differ from the ground "
                "truth. Check your filters and aggregations."
            ),
            expected_shape=expected.shape,
            got_shape=got.shape,
        )
    return Feedback(
        ok=True,
        message="Correct: your result matches the known ground truth exactly.",
        expected_shape=expected.shape,
        got_shape=got.shape,
    )
