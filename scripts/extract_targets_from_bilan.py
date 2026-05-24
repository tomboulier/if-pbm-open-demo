"""Extract per-specialty, per-trimester aggregated targets from the If-PBM bilan.

Reads the (real, aggregated, GDPR-safe) Excel bilan and writes a tidy, shareable
``targets.csv`` that calibrates the synthetic generator. Run once, offline.
"""

from __future__ import annotations

import csv
from pathlib import Path

import openpyxl

BILAN = Path("documentation/bilan_if_pbm_full.xlsx")
OUT = Path("src/if_pbm_open_demo/data/targets.csv")

# Quarterly (rolling 3-month) trimester columns -> (label, start, end).
PERIOD_COLS = {
    5: ("2023-T1", "2023-05-01", "2023-07-31"),
    6: ("2023-T2", "2023-08-01", "2023-10-31"),
    7: ("2023-T3", "2023-11-01", "2024-01-31"),
    8: ("2024-T1", "2024-02-01", "2024-04-30"),
    9: ("2024-T2", "2024-05-01", "2024-07-31"),
    11: ("2024-T3", "2024-08-01", "2024-10-31"),
    12: ("2024-T4", "2024-11-01", "2025-01-31"),
}

# bilan metric label (col0, forward-filled) -> our field name.
METRICS = {
    "n_pat": "n_surgeries",
    "n_cpa": "n_cpa",
    "n_bm_rempli": "n_checkup",
    "n_bm_carence OU": "n_eligible",
    "n_bm_carence_et": "n_corrected",
    "n_transfuses": "n_transfused",
    "n_episodes_trsf": "n_episodes",
    "n_trsf_unitaires": "n_single_unit",
    "n_low_bio_sortie": "n_low_hb",
}
SPECIALTY_MAP = {
    "ortho": "orthopedics",
    "cardio": "cardiology",
    "gyneco_hysterectomie": "gynecology",
    "gyneco_ovariectomie": "gynecology",
}


def clean(v: object) -> int:
    if v is None:
        return 0
    if isinstance(v, str):
        if v.strip() == "<6":
            return 3  # censored small count: use a small placeholder
        return 0  # '#DIV/0!', '-%', etc.
    return int(v)


def match_metric(label: str) -> str | None:
    if "voiron" in label.lower():
        return None  # Voiron sub-totals (e.g. n_pat_voiron) are not separate metrics
    for key, field in METRICS.items():
        if label.startswith(key):
            return field
    return None


def main() -> None:
    wb = openpyxl.load_workbook(BILAN, data_only=True)
    ws = wb["Resultats_agg_5"]
    rows = list(ws.iter_rows(values_only=True))

    # (period_label, specialty) -> {field: value}
    data: dict[tuple[str, str], dict[str, int]] = {}
    meta: dict[str, tuple[str, str]] = {}
    current_field: str | None = None
    for row in rows:
        col0 = row[0]
        if isinstance(col0, str) and col0.strip():
            current_field = match_metric(col0.strip())
        spec_raw = row[1]
        if current_field is None or spec_raw not in SPECIALTY_MAP:
            continue
        specialty = SPECIALTY_MAP[spec_raw]
        for col, (label, start, end) in PERIOD_COLS.items():
            meta[label] = (start, end)
            key = (label, specialty)
            bucket = data.setdefault(key, {})
            bucket[current_field] = bucket.get(current_field, 0) + clean(row[col])

    fields = [
        "n_surgeries",
        "n_cpa",
        "n_checkup",
        "n_eligible",
        "n_corrected",
        "n_transfused",
        "n_episodes",
        "n_single_unit",
        "n_low_hb",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["period_index", "period", "start", "end", "specialty", *fields])
        for i, (label, (start, end)) in enumerate(meta.items()):
            for specialty in ("orthopedics", "cardiology", "gynecology"):
                b = data.get((label, specialty), {})
                vals = {fld: b.get(fld, 0) for fld in fields}
                # enforce simple consistency (caps) for a coherent PoC
                vals["n_cpa"] = min(vals["n_cpa"], vals["n_surgeries"])
                vals["n_checkup"] = min(vals["n_checkup"], vals["n_cpa"])
                vals["n_eligible"] = min(vals["n_eligible"], vals["n_cpa"])
                vals["n_corrected"] = min(vals["n_corrected"], vals["n_eligible"])
                vals["n_transfused"] = min(vals["n_transfused"], vals["n_surgeries"])
                vals["n_episodes"] = max(vals["n_episodes"], vals["n_transfused"])
                vals["n_single_unit"] = min(vals["n_single_unit"], vals["n_episodes"])
                vals["n_low_hb"] = min(vals["n_low_hb"], vals["n_surgeries"])
                w.writerow(
                    [i, label, start, end, specialty, *(vals[f] for f in fields)]
                )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
