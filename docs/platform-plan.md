# Platform plan: from demo to training platform

> Working plan for the `feat/training-platform` branch (overnight build, 2026-06-11).
> Goal stated by Thomas: "faire ces dashboards de manière automatique, et pour cela avoir
> une plateforme de démonstration [...] une super belle plateforme d'entraînement à la
> data science, le tout sur des données réelles (en tout cas agrégées), les données
> d'avant seront synthétiques."

## What exists (baseline, `main`)

- `targets.csv`: real, aggregated, GDPR-safe If-PBM bilan counts (censored `<6` → 3).
- `generate.py`: synthetic patient-level generator calibrated on those counts.
- Canonical schema (input port) + IR1-IR5 SQL + `indicator_results` mart (output port).
- A single-page Streamlit dashboard (overview + per-indicator drill-down).

## What this branch adds

Three pillars, mapping the request:

### 1. Automatic dashboards — indicator registry

A single source of truth, `registry.py`: each indicator carries its key, labels,
clinical definition, numerator/denominator wording, direction (higher/lower is better),
year-2 targets per specialty (from the Article 51 cahier des charges), and its SQL file.
Dashboard pages, KPI status colours, target bands, and training-exercise validation are
all **derived** from the registry. Adding an IR6 = one SQL file + one registry entry;
the platform grows a page, a KPI tile, and a target band with zero dashboard code.

Year-2 targets (cahier des charges): IR1 ≥90% (all); IR2 ortho ≥75%, cardio ≥65%,
gyneco ≥65%; IR3 ≥40% (all); IR4 ortho ≤5%, cardio ≤25% (gyneco split
hysterectomy ≤7% / ovariectomy ≤15% — schema has only `gynecology`, so no single
gyneco target is displayed for IR4/IR5; a registry note documents the split).
IR5 ≤25% (ortho/cardio; gyneco split 50/65 with Hb<9, same note). The official
criterion is "reach the target OR improve by X% vs T0", so the UI always says
"year-2 target", never an absolute threshold.

### 2. Demonstration platform — dashboard v2 + real-vs-synthetic calibration

- Multi-page Streamlit app (`st.navigation`), styled after the validated mockups
  (`documentation/maquettes dashboards.pptx`): cream background, blue-grey panels,
  KPI discs coloured by target status, target bands on charts.
- **Overview**: cohort header, per-indicator KPI discs (latest period, status vs
  target, trend delta), small multiples of the five trends.
- **One page per indicator**, generated from the registry: trend with target band
  and per-specialty lines, latest-period bars, underlying counts, clinical definition.
- **Calibration page (real vs synthetic)**: the official, real aggregated IR values
  (ortho/cardio) read from the bilan's published "IR" rows are shipped as
  `data/real_ir.csv` and overlaid on the synthetic-pipeline results. This is the
  "known ground truth" claim of the PRFAQ made visible: the synthetic data reproduces
  the real aggregated trajectories.
  - Provenance: the bilan's IR rows use the official "eligible excluding Voiron"
    denominator and were censored (`<6`) **at the source**; only aggregated
    proportions already public in presentations are shipped. The source xlsx stays
    untracked, as today. Gynecology is not shipped quarterly (volumes too small;
    censored at source).

### 3. Training platform — "Learn" track with auto-validation

`training.py`: progressive, self-correcting SQL exercises against the synthetic
clinical data warehouse, validated **automatically against the known ground truth**
(the mart). Each exercise = statement, starter query, hint(s), reference solution,
and a validator that compares the learner's result to the expected one and explains
mismatches (missing columns, wrong row count, wrong values). Levels:

1. Explore the warehouse (counts, joins, the period dimension).
2. Recompute IR1 (eligibility + checkup) and match the mart exactly.
3. Recompute IR4 (distinct transfused patients).
4. Recompute IR3 (transfusion *episodes* with the 1-hour window — the hard one).
5. Open challenge: low-Hb discharge (IR5) and free exploration.

The Learn pages and the SQL playground read the **canonical tables** on purpose:
that is the teaching surface. BI pages (overview, indicators) keep reading only the
mart, preserving the output-port discipline.

## Non-goals (tonight)

- No Superset/real-CDW adapter, no OMOP/FHIR mapping (research agenda, not tonight).
- No deployment (Docker/HF Space) — the platform must run with `uv run if-pbm-demo demo`.
- No authentication, no persistence of learner progress beyond the session.

## Quality bar

- `pytest`, `ruff check`, `ruff format --check`, `mypy --strict src/` all green.
- Visual QA of every page (Playwright screenshots) before declaring done.
- Conventional commits, one logical change each.
