"""Extract the official, real aggregated IR proportions from the If-PBM bilan.

Reads the (real, aggregated, GDPR-safe) Excel bilan and writes a tidy
``real_ir.csv`` shipped with the package. Run once, offline; the source xlsx
stays untracked.

Provenance notes (they matter for any comparison):

- The "IR" rows are computed by the upstream production pipeline with the
  official "eligible excluding Voiron" denominator, which is NOT recomputable
  from the shipped count layer (``targets.csv``). Synthetic results therefore
  track these values closely, not exactly.
- Small-count censoring (``<6`` -> ``-%``) was applied AT THE SOURCE; censored
  cells become empty proportions here.
- Orthopedics / cardiology are quarterly; gynecology volumes are too small for
  quarterly reporting and only exist as a one-year bilan, split by procedure
  (hysterectomy / ovariectomy), kept under the ``1Y`` period label.
"""

from __future__ import annotations

import csv
from pathlib import Path

import openpyxl

BILAN = Path("documentation/bilan_if_pbm_full.xlsx")
OUT = Path("src/if_pbm_open_demo/data/real_ir.csv")
SHEET = "Resultats_agg_5"

#: Quarterly bilan columns (0-based) -> period label, as in targets.csv.
QUARTER_COLS = {
    5: "2023-T1",
    6: "2023-T2",
    7: "2023-T3",
    8: "2024-T1",
    9: "2024-T2",
    11: "2024-T3",
    12: "2024-T4",
}
ANNUAL_COL = 10  # "Bilan 1 an gyneco"

#: bilan specialty label -> (output specialty, reported scope).
SPECIALTIES = {
    "ortho": ("orthopedics", "quarterly"),
    "cardio": ("cardiology", "quarterly"),
    "gyneco_hysterectomie": ("gynecology_hysterectomy", "annual"),
    "gyneco_ovariectomie": ("gynecology_ovariectomy", "annual"),
}


def parse_proportion(cell: object) -> float | None:
    """A proportion in [0, 1], or None when censored / not computable."""
    if cell is None:
        return None
    text = str(cell).strip()
    if text == "" or text in ("-%", "#DIV/0!") or "<" in text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if 0.0 <= value <= 1.0 else None


def main() -> None:
    wb = openpyxl.load_workbook(BILAN, data_only=True)
    rows = list(wb[SHEET].iter_rows(values_only=True))

    records: list[tuple[str, str, str, float | None]] = []
    current_ir: str | None = None
    for row in rows:
        label = row[0]
        if label is not None and str(label).strip():
            text = str(label).strip()
            current_ir = text[:3] if text.upper().startswith("IR") else None
        spec_raw = row[1]
        if current_ir is None or spec_raw not in SPECIALTIES:
            continue
        specialty, scope = SPECIALTIES[str(spec_raw)]
        if scope == "quarterly":
            for col, period in QUARTER_COLS.items():
                records.append(
                    (current_ir, specialty, period, parse_proportion(row[col]))
                )
        else:
            records.append(
                (current_ir, specialty, "1Y", parse_proportion(row[ANNUAL_COL]))
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["indicator", "specialty", "period", "proportion"])
        for indicator, specialty, period, proportion in records:
            writer.writerow(
                [
                    indicator,
                    specialty,
                    period,
                    "" if proportion is None else f"{proportion:.6f}",
                ]
            )
    print(f"wrote {OUT} ({len(records)} rows)")


if __name__ == "__main__":
    main()
