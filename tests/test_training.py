"""The training engine validates attempts against the known ground truth."""

from pathlib import Path

import pytest

from if_pbm_open_demo.pipeline import build
from if_pbm_open_demo.training import EXERCISES, by_key, check_attempt


@pytest.fixture(scope="module")
def db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("training") / "if_pbm.duckdb"
    build(path)
    return path


def test_exercises_are_progressive_and_documented() -> None:
    assert len(EXERCISES) >= 5
    levels = [e.level for e in EXERCISES]
    assert levels == sorted(levels)
    for exercise in EXERCISES:
        assert exercise.hints, exercise.key
        assert exercise.statement and exercise.solution_sql, exercise.key


def test_every_reference_solution_passes_its_own_exercise(db_path: Path) -> None:
    for exercise in EXERCISES:
        feedback = check_attempt(db_path, exercise, exercise.solution_sql)
        assert feedback.ok, f"{exercise.key}: {feedback.message}"


def test_indicator_exercises_match_the_official_mart(db_path: Path) -> None:
    """Recomputing IR1 via the exercise equals the mart the dashboards read."""
    attempt = (
        "SELECT specialty, period, numerator, denominator "
        "FROM indicator_results WHERE indicator = 'IR1'"
    )
    feedback = check_attempt(db_path, by_key("ir1"), attempt)
    assert feedback.ok, feedback.message


def test_row_order_and_column_case_do_not_matter(db_path: Path) -> None:
    attempt = (
        "SELECT count(*) AS N_SURGERIES, specialty AS SPECIALTY "
        "FROM surgery GROUP BY specialty ORDER BY specialty DESC"
    )
    assert check_attempt(db_path, by_key("cohort"), attempt).ok


def test_wrong_columns_yield_actionable_feedback(db_path: Path) -> None:
    feedback = check_attempt(
        db_path,
        by_key("cohort"),
        "SELECT specialty, count(*) AS n FROM surgery GROUP BY 1",
    )
    assert not feedback.ok
    assert "n_surgeries" in feedback.message


def test_wrong_values_are_rejected(db_path: Path) -> None:
    feedback = check_attempt(
        db_path,
        by_key("cohort"),
        "SELECT specialty, count(*) + 1 AS n_surgeries FROM surgery GROUP BY specialty",
    )
    assert not feedback.ok
    assert "row(s) differ" in feedback.message


def test_broken_sql_is_reported_not_raised(db_path: Path) -> None:
    feedback = check_attempt(db_path, by_key("cohort"), "SELEC oops")
    assert not feedback.ok
    assert "failed" in feedback.message
