# If-PBM Open Demo

![CI](https://github.com/tomboulier/if-pbm-open-demo/actions/workflows/ci.yml/badge.svg)

Reproducible, open-source demo of the **If-PBM** Patient Blood Management (PBM) monitoring
method described in the MIE2026 short communication *"Monitoring adherence to PBM guidelines
from clinical data warehouse: a case study"* (Beaudoin, Godon, Marquet, Boulier,
Moreau-Gaudry, Grenoble Alpes University Hospital).

It generates **synthetic** clinical data, computes the **five If-PBM indicators (IR1-IR5)**
across orthopedics, cardiology, and gynecology by trimester, and serves an interactive
dashboard. No real patient data is involved.

## What it shows

| Indicator | Definition |
|-----------|------------|
| IR1 | Proportion of standardized PBM preoperative check-ups |
| IR2 | Proportion of corrective treatments for anemia / iron deficiency |
| IR3 | Proportion of single-unit transfusion episodes |
| IR4 | Proportion of patients transfused per- or post-operatively |
| IR5 | Proportion of patients discharged with low hemoglobin |

## Architecture

The method is decoupled behind two stable seams (ports), so inputs and outputs are swappable:

```
 input adapters       canonical schema        indicators (SQL)      results mart        output adapters
 synthetic (here) ──▶ patient / surgery / ──▶ IR1..IR5 over     ──▶ indicator_results ─▶ Streamlit (here)
 real CDW (later)     transfusion / lab /      the canonical         (indicator x          Superset (later)
                      consultation             schema, in DuckDB     specialty x quarter)
```

- **Input port** = the canonical schema. A real CDW adapter would simply produce conforming rows.
- **Output port** = the `indicator_results` table. Any BI tool (Streamlit here, Superset for
  D2H later) reads the same mart without touching the computation.

## Install

```bash
# Recommended: uv
uv tool install git+https://github.com/tomboulier/if-pbm-open-demo

# Or from a clone, for development
git clone https://github.com/tomboulier/if-pbm-open-demo
cd if-pbm-open-demo
uv sync
```

## Run

One command generates data, computes indicators, and launches the dashboard:

```bash
uv run if-pbm-demo demo
```

Or step by step:

```bash
uv run if-pbm-demo generate     # synthetic canonical data -> data/if_pbm.duckdb
uv run if-pbm-demo indicators   # compute IR1-IR5 -> indicator_results mart
uv run if-pbm-demo dashboard    # launch the Streamlit dashboard
```

## Note on data

All data is synthetic, generated from a seeded model with tunable per-specialty adherence
trends (see `src/if_pbm_open_demo/generate.py`). It is designed to reproduce plausible,
specialty-differentiated indicator trajectories, **not** to reflect real patients.
