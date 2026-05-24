"""Synthetic data generator: one input adapter producing the canonical schema.

This is an *inverse* construction. The real, aggregated If-PBM bilan (shipped as the
shareable, GDPR-safe ``data/targets.csv``) gives, per specialty and trimester, the
counts the indicators are built from. The generator invents patient-level rows
engineered so that, once aggregated by the indicator SQL, they reproduce those counts.
The runtime pipeline matches production: patient data -> aggregate -> indicators.

It is a proof of concept: counts are reproduced closely, not necessarily to the unit.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from importlib import resources

import numpy as np
import pandas as pd

from .schema import LOW_HB_THRESHOLD_G_DL

LOW_HB_VALUE = LOW_HB_THRESHOLD_G_DL - 1.5  # clearly below the threshold
NORMAL_HB_VALUE = LOW_HB_THRESHOLD_G_DL + 1.5  # clearly above the threshold


@dataclass(frozen=True)
class Target:
    """Aggregated targets for one (period, specialty) cell of the bilan."""

    period: str
    start: date
    end: date
    specialty: str
    n_surgeries: int
    n_cpa: int
    n_checkup: int
    n_eligible: int
    n_corrected: int
    n_transfused: int
    n_episodes: int
    n_single_unit: int
    n_low_hb: int


def load_targets() -> list[Target]:
    """Load the calibration targets shipped with the package."""
    text = (
        resources.files(f"{__package__}.data")
        .joinpath("targets.csv")
        .read_text("utf-8")
    )
    targets: list[Target] = []
    for row in csv.DictReader(text.splitlines()):
        targets.append(
            Target(
                period=row["period"],
                start=date.fromisoformat(row["start"]),
                end=date.fromisoformat(row["end"]),
                specialty=row["specialty"],
                n_surgeries=int(row["n_surgeries"]),
                n_cpa=int(row["n_cpa"]),
                n_checkup=int(row["n_checkup"]),
                n_eligible=int(row["n_eligible"]),
                n_corrected=int(row["n_corrected"]),
                n_transfused=int(row["n_transfused"]),
                n_episodes=int(row["n_episodes"]),
                n_single_unit=int(row["n_single_unit"]),
                n_low_hb=int(row["n_low_hb"]),
            )
        )
    return targets


def period_dimension() -> pd.DataFrame:
    """Return the reporting calendar (distinct periods with their date ranges)."""
    seen: dict[str, tuple[date, date]] = {}
    for tgt in load_targets():
        seen[tgt.period] = (tgt.start, tgt.end)
    return pd.DataFrame(
        [{"period": p, "start_date": s, "end_date": e} for p, (s, e) in seen.items()],
        columns=["period", "start_date", "end_date"],
    )


@dataclass
class _Ids:
    patient: int = 1
    surgery: int = 1
    consultation: int = 1
    lab: int = 1
    transfusion: int = 1


def _random_date(rng: np.random.Generator, start: date, end: date) -> date:
    span = max((end - start).days, 1)
    return start + timedelta(days=int(rng.integers(0, span + 1)))


def generate(seed: int = 42) -> dict[str, pd.DataFrame]:
    """Generate canonical tables calibrated to reproduce the aggregated bilan.

    Parameters
    ----------
    seed:
        Seed for reproducibility; the same seed yields identical data.

    Returns
    -------
    dict of str to pandas.DataFrame
        One DataFrame per canonical table, columns in canonical-schema order.
    """
    rng = np.random.default_rng(seed)
    ids = _Ids()
    patients: list[dict[str, object]] = []
    surgeries: list[dict[str, object]] = []
    consultations: list[dict[str, object]] = []
    labs: list[dict[str, object]] = []
    transfusions: list[dict[str, object]] = []

    for tgt in load_targets():
        _build_cell(
            rng, ids, tgt, patients, surgeries, consultations, labs, transfusions
        )

    return {
        "patient": pd.DataFrame(patients, columns=["patient_id", "birth_year", "sex"]),
        "surgery": pd.DataFrame(
            surgeries, columns=["surgery_id", "patient_id", "specialty", "surgery_date"]
        ),
        "consultation": pd.DataFrame(
            consultations,
            columns=[
                "consultation_id",
                "patient_id",
                "surgery_id",
                "consultation_date",
                "pbm_checkup_done",
                "anemia_detected",
                "anemia_corrected",
            ],
        ),
        "lab": pd.DataFrame(
            labs,
            columns=[
                "lab_id",
                "patient_id",
                "surgery_id",
                "test",
                "value",
                "unit",
                "sample_datetime",
            ],
        ),
        "transfusion": pd.DataFrame(
            transfusions,
            columns=[
                "transfusion_id",
                "patient_id",
                "surgery_id",
                "product_type",
                "delivery_datetime",
            ],
        ),
    }


def _build_cell(
    rng: np.random.Generator,
    ids: _Ids,
    tgt: Target,
    patients: list[dict[str, object]],
    surgeries: list[dict[str, object]],
    consultations: list[dict[str, object]],
    labs: list[dict[str, object]],
    transfusions: list[dict[str, object]],
) -> None:
    """Construct patient-level rows for one (period, specialty) cell."""
    surgery_ids: list[int] = []
    for i in range(tgt.n_surgeries):
        patient_id = ids.patient
        ids.patient += 1
        patients.append(
            {
                "patient_id": patient_id,
                "birth_year": int(rng.integers(1940, 2005)),
                "sex": "F" if rng.random() < 0.5 else "M",
            }
        )
        surgery_id = ids.surgery
        ids.surgery += 1
        surgery_ids.append(surgery_id)
        s_date = _random_date(rng, tgt.start, tgt.end)
        surgeries.append(
            {
                "surgery_id": surgery_id,
                "patient_id": patient_id,
                "specialty": tgt.specialty,
                "surgery_date": s_date,
            }
        )

        # Discharge hemoglobin lab (drives IR5). First n_low_hb surgeries are "low".
        is_low = i < tgt.n_low_hb
        labs.append(
            {
                "lab_id": ids.lab,
                "patient_id": patient_id,
                "surgery_id": surgery_id,
                "test": "hemoglobin",
                "value": LOW_HB_VALUE if is_low else NORMAL_HB_VALUE,
                "unit": "g/dL",
                "sample_datetime": datetime.combine(
                    s_date + timedelta(days=int(rng.integers(1, 15))), time(8, 0)
                ),
            }
        )
        ids.lab += 1

        # Pre-anesthesia consultation (drives IR1/IR2) for the first n_cpa surgeries.
        if i < tgt.n_cpa:
            consultations.append(
                {
                    "consultation_id": ids.consultation,
                    "patient_id": patient_id,
                    "surgery_id": surgery_id,
                    "consultation_date": s_date
                    - timedelta(days=int(rng.integers(3, 30))),
                    "pbm_checkup_done": i < tgt.n_checkup,
                    "anemia_detected": i < tgt.n_eligible,
                    "anemia_corrected": i < tgt.n_corrected,
                }
            )
            ids.consultation += 1

    _build_transfusions(rng, ids, tgt, surgery_ids, surgeries, transfusions)


def _build_transfusions(
    rng: np.random.Generator,
    ids: _Ids,
    tgt: Target,
    surgery_ids: list[int],
    surgeries: list[dict[str, object]],
    transfusions: list[dict[str, object]],
) -> None:
    """Attach transfusion episodes to reproduce IR3 (episodes) and IR4 (transfused)."""
    if tgt.n_transfused == 0 or not surgery_ids:
        return
    transfused = surgery_ids[: tgt.n_transfused]
    surgery_date = {s["surgery_id"]: s["surgery_date"] for s in surgeries}
    patient_of = {s["surgery_id"]: s["patient_id"] for s in surgeries}

    # One episode per transfused surgery; spread remaining episodes round-robin.
    episode_surgeries = list(transfused)
    extra = max(tgt.n_episodes - tgt.n_transfused, 0)
    for k in range(extra):
        episode_surgeries.append(transfused[k % len(transfused)])

    # Which episodes are single-unit (1 RBC) vs multi-unit (2 RBC < 1h apart).
    single_flags = [j < tgt.n_single_unit for j in range(len(episode_surgeries))]
    episode_rank: dict[int, int] = {}
    for surgery_id, is_single in zip(episode_surgeries, single_flags, strict=True):
        rank = episode_rank.get(surgery_id, 0)
        episode_rank[surgery_id] = rank + 1
        s_date = surgery_date[surgery_id]
        assert isinstance(s_date, date)
        # Episodes for the same surgery are >1h apart so the SQL keeps them separate.
        base = datetime.combine(
            s_date + timedelta(days=int(rng.integers(0, 5))), time(9, 0)
        ) + timedelta(hours=3 * rank)
        n_units = 1 if is_single else 2
        for u in range(n_units):
            transfusions.append(
                {
                    "transfusion_id": ids.transfusion,
                    "patient_id": patient_of[surgery_id],
                    "surgery_id": surgery_id,
                    "product_type": "RBC",
                    "delivery_datetime": base + timedelta(minutes=15 * u),
                }
            )
            ids.transfusion += 1
