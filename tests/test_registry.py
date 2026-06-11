"""The indicator registry is the single source of truth for the platform."""

from importlib import resources

import pytest

from if_pbm_open_demo.registry import INDICATORS, SPECIALTIES, by_key


def test_registry_lists_the_five_indicators_in_order() -> None:
    assert [ind.key for ind in INDICATORS] == ["IR1", "IR2", "IR3", "IR4", "IR5"]


def test_every_indicator_points_to_an_existing_sql_file() -> None:
    sql_dir = resources.files("if_pbm_open_demo.sql")
    for ind in INDICATORS:
        assert sql_dir.joinpath(ind.sql_file).is_file(), ind.key


def test_directions_follow_the_cahier_des_charges() -> None:
    higher = {"IR1", "IR2", "IR3"}
    for ind in INDICATORS:
        expected = "higher_is_better" if ind.key in higher else "lower_is_better"
        assert ind.direction == expected, ind.key


def test_year2_targets_are_specialty_specific() -> None:
    ir2, ir4 = by_key("IR2"), by_key("IR4")
    assert ir2.targets["orthopedics"] == pytest.approx(0.75)
    assert ir2.targets["cardiology"] == pytest.approx(0.65)
    assert ir4.targets["orthopedics"] == pytest.approx(0.05)
    assert ir4.targets["cardiology"] == pytest.approx(0.25)
    # Gynecology IR4/IR5 are split hysterectomy/ovariectomy in the cahier des
    # charges; the canonical schema only has 'gynecology', so no single target.
    assert ir4.targets["gynecology"] is None
    assert ir4.target_note is not None


def test_every_indicator_covers_every_specialty() -> None:
    for ind in INDICATORS:
        assert set(ind.targets) == set(SPECIALTIES), ind.key


def test_status_compares_a_value_to_the_target_in_the_right_direction() -> None:
    ir1, ir4 = by_key("IR1"), by_key("IR4")
    assert ir1.status(0.92, "orthopedics") == "met"
    assert ir1.status(0.50, "orthopedics") == "missed"
    assert ir4.status(0.03, "orthopedics") == "met"
    assert ir4.status(0.07, "orthopedics") == "missed"
    assert ir4.status(0.10, "gynecology") == "no_target"
    assert ir4.status(None, "orthopedics") == "no_data"


def test_by_key_rejects_unknown_indicators() -> None:
    with pytest.raises(KeyError):
        by_key("IR9")
