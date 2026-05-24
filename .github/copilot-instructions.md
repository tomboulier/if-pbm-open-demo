# GitHub Copilot instructions

Reproducible open-source demo of the If-PBM PBM monitoring method: synthetic data → five
indicators (IR1-IR5) as DuckDB SQL → Streamlit dashboard. All data is synthetic.

## Architecture (two seams)

- Input port = canonical schema (patient, surgery, transfusion, lab, consultation).
  Indicators depend only on this schema.
- Output port = the `indicator_results` mart. The dashboard reads only the mart.
- One adapter per side today (synthetic in, Streamlit out); keep seams clean for future
  real-CDW input and Superset output adapters.

## Stack

Python 3.12, uv, DuckDB, pandas, Streamlit, plotly.

## Conventions

- Conventional Commits; imperative mood, English, ≤72 chars, no trailing period.
- Test-driven development: write tests before implementation.
- Type hints everywhere; numpydoc docstrings.
- KISS, YAGNI, SOLID.

## Avoid

- Out-of-scope refactors, unrequested features, redundant comments.
- Any real patient data; this project is synthetic-only.
