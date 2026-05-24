from pathlib import Path

import duckdb

from if_pbm_open_demo.generate import load_targets
from if_pbm_open_demo.pipeline import build

# (indicator, numerator field, denominator field) for each target cell.
EXPECTED = {
    "IR1": ("n_checkup", "n_cpa"),
    "IR2": ("n_corrected", "n_eligible"),
    "IR3": ("n_single_unit", "n_episodes"),
    "IR4": ("n_transfused", "n_surgeries"),
    "IR5": ("n_low_hb", "n_surgeries"),
}


def test_aggregation_reproduces_bilan(tmp_path: Path) -> None:
    db = build(tmp_path / "demo.duckdb", seed=1)
    con = duckdb.connect(str(db), read_only=True)
    try:
        rows = con.execute(
            "SELECT indicator, specialty, period, numerator, denominator "
            "FROM indicator_results"
        ).fetchall()
    finally:
        con.close()

    actual = {(r[0], r[1], r[2]): (r[3], r[4]) for r in rows}

    checked = 0
    for tgt in load_targets():
        for indicator, (num_field, den_field) in EXPECTED.items():
            exp_num = getattr(tgt, num_field)
            exp_den = getattr(tgt, den_field)
            if exp_den == 0:
                continue
            key = (indicator, tgt.specialty, tgt.period)
            assert key in actual, f"missing {key}"
            assert actual[key] == (exp_num, exp_den), (
                f"{key}: got {actual[key]}, expected {(exp_num, exp_den)}"
            )
            checked += 1
    assert checked > 100  # sanity: we actually compared many cells
