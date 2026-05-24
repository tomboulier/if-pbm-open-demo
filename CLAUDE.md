# CLAUDE.md

## Project

Reproducible open-source demo of the If-PBM PBM monitoring method: synthetic data → five
indicators (IR1-IR5) as DuckDB SQL → Streamlit dashboard. All data is synthetic.

## Architecture (two seams)

- **Input port** = canonical schema (patient, surgery, transfusion, lab, consultation).
  Indicators depend only on this schema, never on a specific source.
- **Output port** = the `indicator_results` mart. The dashboard reads only the mart.
- One adapter per side today (synthetic in, Streamlit out). Keep the seams clean so a
  real-CDW input or a Superset output can be added without touching the domain.

## Stack & commands

Python 3.12, uv, DuckDB, pandas, Streamlit, plotly.

```bash
uv sync --extra dev          # install
uv run if-pbm-demo demo      # generate + compute + dashboard
uv run pytest                # tests
uv run ruff check . && uv run ruff format --check . && uv run mypy src/
```

## Conventions

- Conventional Commits; imperative, English, ≤72 chars, no trailing period.
- TDD: tests before implementation.
- Type hints everywhere; numpydoc docstrings.
- KISS, YAGNI, SOLID.

## Do not

- Refactor outside the scope of the task.
- Add features that were not requested.
- Write comments that merely restate the code.
- Connect to or assume any real patient data; this project is synthetic-only.
