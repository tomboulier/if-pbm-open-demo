# CLAUDE.md

## Project

Reproducible open-source platform around the If-PBM PBM monitoring method: synthetic
warehouse (calibrated on the real aggregated bilan) → five indicators (IR1-IR5) as
DuckDB SQL → Streamlit platform (dashboards + calibration + training track). All
patient-level data is synthetic; only aggregated, source-censored values are shipped.

## Architecture (two seams + one registry)

- **Input port** = canonical schema (patient, surgery, transfusion, lab, consultation).
  Indicators depend only on this schema, never on a specific source.
- **Output port** = the `indicator_results` mart. BI pages (overview, indicator pages)
  read only the mart. Exception by design: the explorer and Learn pages read the
  canonical tables, because the warehouse is their teaching surface.
- **Registry** (`registry.py`) = single source of truth per indicator: labels,
  definition, direction, year-2 targets per specialty, SQL file. Dashboard pages, KPI
  status colours, target bands, and exercise validation derive from it. Adding an
  indicator = one SQL file + one registry entry.
- `reference.py` / `data/real_ir.csv` = real aggregated official IR values (denominator
  "eligible excluding Voiron", censored at the source, NOT recomputable from
  `targets.csv`). Extraction scripts in `scripts/` run offline against the untracked
  `documentation/bilan_if_pbm_full.xlsx`.
- `training.py` = Streamlit-free exercise engine (statements, hints, reference
  solutions, result comparison). `dashboard/views/learn.py` is only rendering.
- The Streamlit package is `dashboard/` with pages in `dashboard/views/`: do NOT name
  that directory `pages/`, Streamlit auto-discovers any `pages/` dir next to the entry
  script and breaks the navigation.

## Stack & commands

Python 3.12, uv, DuckDB, pandas, Streamlit (st.navigation), plotly.

```bash
uv sync --extra dev          # install
uv run if-pbm-demo demo      # generate + compute + platform
uv run pytest                # tests
uv run ruff check . && uv run ruff format --check . && uv run mypy src/
```

## Conventions

- Conventional Commits; imperative, English, ≤72 chars, no trailing period.
- TDD: tests before implementation.
- Type hints everywhere (mypy strict); numpydoc docstrings.
- KISS, YAGNI, SOLID.
- Visual identity in `dashboard/theme.py` only (mockup palette: cream page, blue-grey
  panels, KPI discs coloured by target status); pages stay declarative.

## Do not

- Refactor outside the scope of the task.
- Add features that were not requested.
- Write comments that merely restate the code.
- Connect to or assume any real patient data; patient-level data is synthetic-only.
- Re-censor or recompute the shipped real aggregated values: `real_ir.csv` is read
  as published (censoring already applied upstream).
