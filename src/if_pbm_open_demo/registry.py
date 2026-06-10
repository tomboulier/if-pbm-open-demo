"""Indicator registry: the single source of truth for the platform.

Every indicator is described once, here: clinical wording, computation contract
(numerator / denominator / SQL file), direction of improvement, and the year-2
targets from the If-PBM Article 51 cahier des charges. Dashboard pages, KPI status
colours, target bands, and training-exercise validation are all derived from this
registry, so adding an indicator means adding one SQL file and one entry below.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

#: Specialties of the If-PBM perimeter, in display order.
SPECIALTIES: tuple[str, ...] = ("orthopedics", "cardiology", "gynecology")

#: Human-readable specialty labels.
SPECIALTY_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "orthopedics": "Orthopedics",
        "cardiology": "Cardiology",
        "gynecology": "Gynecology",
    }
)

Direction = Literal["higher_is_better", "lower_is_better"]
Status = Literal["met", "missed", "no_target", "no_data"]

#: Note attached to gynecology targets that the cahier des charges splits by
#: procedure; the canonical schema only carries the specialty, so no single
#: gynecology target can be displayed for those indicators.
_GYN_SPLIT_IR4 = (
    "Gynecology year-2 targets are split by procedure in the cahier des charges "
    "(hysterectomy <= 7%, ovariectomy <= 15%); the canonical schema does not "
    "distinguish them, so no single gynecology target is shown."
)
_GYN_SPLIT_IR5 = (
    "Gynecology year-2 targets are split by procedure in the cahier des charges "
    "(hysterectomy <= 50%, ovariectomy <= 65%, with a 9 g/dL threshold instead "
    "of 10); the canonical schema does not distinguish them, so no single "
    "gynecology target is shown."
)


@dataclass(frozen=True)
class Indicator:
    """One If-PBM result indicator, fully described."""

    key: str
    title: str
    short_label: str
    definition: str
    numerator: str
    denominator: str
    direction: Direction
    targets: Mapping[str, float | None]
    sql_file: str
    icon: str
    target_note: str | None = None

    @property
    def comparator(self) -> str:
        """The symbol relating a good value to the target (>= or <=)."""
        return ">=" if self.direction == "higher_is_better" else "<="

    def status(self, value: float | None, specialty: str) -> Status:
        """Compare a proportion to the year-2 target for one specialty."""
        if value is None:
            return "no_data"
        target = self.targets.get(specialty)
        if target is None:
            return "no_target"
        if self.direction == "higher_is_better":
            return "met" if value >= target else "missed"
        return "met" if value <= target else "missed"


def _targets(**values: float | None) -> Mapping[str, float | None]:
    """Build an immutable specialty -> target mapping covering all specialties."""
    mapping = {spec: values[spec] for spec in SPECIALTIES}
    return MappingProxyType(mapping)


#: The five If-PBM result indicators, in reporting order.
INDICATORS: tuple[Indicator, ...] = (
    Indicator(
        key="IR1",
        title="Preoperative PBM check-up",
        short_label="Preop check-up",
        definition=(
            "Proportion of standardized PBM preoperative check-ups (anemia and/or "
            "iron-deficiency screening) among surgeries with a pre-anesthesia "
            "consultation."
        ),
        numerator="Consultations recording a standardized PBM check-up",
        denominator="Surgeries with a pre-anesthesia consultation",
        direction="higher_is_better",
        targets=_targets(orthopedics=0.90, cardiology=0.90, gynecology=0.90),
        sql_file="ir1.sql",
        icon="🩺",
    ),
    Indicator(
        key="IR2",
        title="Anemia / iron correction",
        short_label="Anemia correction",
        definition=(
            "Proportion of corrective treatments (iron, EPO) among patients with "
            "preoperative anemia and/or iron deficiency detected at the "
            "pre-anesthesia consultation."
        ),
        numerator="Eligible patients who received a corrective treatment",
        denominator="Patients with anemia / iron deficiency detected",
        direction="higher_is_better",
        targets=_targets(orthopedics=0.75, cardiology=0.65, gynecology=0.65),
        sql_file="ir2.sql",
        icon="💊",
    ),
    Indicator(
        key="IR3",
        title="Single-unit transfusion",
        short_label="Single-unit",
        definition=(
            "Proportion of single-unit red-blood-cell transfusion episodes among "
            "all per/post-operative episodes (units less than one hour apart "
            "belong to the same episode)."
        ),
        numerator="Episodes delivering exactly one RBC unit",
        denominator="All per/post-operative transfusion episodes",
        direction="higher_is_better",
        targets=_targets(orthopedics=0.40, cardiology=0.40, gynecology=0.40),
        sql_file="ir3.sql",
        icon="🩸",
    ),
    Indicator(
        key="IR4",
        title="Transfused patients",
        short_label="Transfused",
        definition=(
            "Proportion of patients transfused per- or post-operatively (at least "
            "one RBC unit within 30 days of surgery) among operated patients."
        ),
        numerator="Operated patients with at least one RBC unit",
        denominator="All operated patients",
        direction="lower_is_better",
        targets=_targets(orthopedics=0.05, cardiology=0.25, gynecology=None),
        sql_file="ir4.sql",
        icon="🏥",
        target_note=_GYN_SPLIT_IR4,
    ),
    Indicator(
        key="IR5",
        title="Low discharge hemoglobin",
        short_label="Low discharge Hb",
        definition=(
            "Proportion of patients discharged with a low hemoglobin (last value "
            "below 10 g/dL within 30 days of surgery) among operated patients "
            "with a discharge measurement."
        ),
        numerator="Patients whose last post-operative Hb is below the threshold",
        denominator="Operated patients with a post-operative Hb measurement",
        direction="lower_is_better",
        targets=_targets(orthopedics=0.25, cardiology=0.25, gynecology=None),
        sql_file="ir5.sql",
        icon="🔬",
        target_note=_GYN_SPLIT_IR5,
    ),
)


def by_key(key: str) -> Indicator:
    """Return the indicator with the given key, or raise ``KeyError``."""
    for indicator in INDICATORS:
        if indicator.key == key:
            return indicator
    raise KeyError(f"unknown indicator: {key!r}")
