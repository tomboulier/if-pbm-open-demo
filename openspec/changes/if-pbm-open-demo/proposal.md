## Why

The If-PBM program (French national funding for Patient Blood Management) requires funded
centers to produce dashboards monitoring adherence to PBM guidelines. Grenoble Alpes
University Hospital built such a system and described its method in the MIE2026 short
communication "Monitoring adherence to PBM guidelines from clinical data warehouse".

Today that system is **not reproducible or transferable**:
- orchestration relies on proprietary Talend jobs,
- ingestion depends on manual monthly CSV exports placed at hardcoded Windows paths,
- the data is hospital-internal and cannot be shared,
- the published output is tables, not the actual dashboards stakeholders want.

We want an **open, runnable demo** that proves the method works end to end on synthetic
data, with one command, from a public repository. It serves four needs, in priority order:
1. a reproducibility companion to the MIE2026 paper (deadline: presentation day),
2. a transferable toolkit other If-PBM-funded centers can repoint at their own data,
3. a clean re-architecture that escapes Talend and manual exports,
4. a presentation-ready demo (forced shape, given the deadline).

## What Changes

- Introduce a **canonical data contract** (patient / surgery / transfusion / lab /
  consultation) that any data source conforms to. This is the input port.
- Add a **synthetic data generator** (one input adapter) calibrated to the real aggregated
  bilan (shipped as a shareable, GDPR-safe `targets.csv`): it constructs patient-level rows
  across orthopedics, cardiology, and gynecology so that, once aggregated, the indicators
  reproduce the published per-specialty, per-trimester values. It does not invent values.
- Compute the **five PBM indicators (IR1-IR5)** as readable SQL over the canonical schema,
  materializing results into a stable `indicator_results` mart. This mart is the output port.
- Ship a **Streamlit dashboard** that reads only the mart and renders trends by quarter and
  specialty (replacing tables as the primary output).
- Provide a **clone-and-run experience**: `pip install` + one command, no server required.

Out of scope for this change (deliberately): a Superset output adapter, a real-CDW input
adapter, an ArangoDB/AQL graph layer. The architecture keeps these cheap to add later by
isolating them behind the two ports, but we implement exactly one adapter on each side now.

## Capabilities

### New Capabilities
- `synthetic-data-generation`: generate synthetic clinical records conforming to the
  canonical data contract, with controllable adherence trends over time and by specialty.
- `pbm-indicators`: compute IR1-IR5 over the canonical schema and materialize an
  `indicator_results` mart keyed by indicator, specialty, and quarter.
- `indicator-dashboard`: a Streamlit dashboard rendering indicator trends from the mart,
  decoupled from the compute and storage engine.

### Modified Capabilities
<!-- None. This is a greenfield demo; no existing specs change. -->

## Impact

- New repository scaffold (Python project): synthetic generator, DuckDB-backed indicator
  SQL, Streamlit app, README with one-command run.
- New dependencies: `duckdb`, `streamlit`, a data/plotting stack (e.g. `pandas`,
  `plotly`/`altair`), and `numpy`/standard-library `random` for the synthetic generator.
- No connection to real hospital systems; all data is synthetic and shareable.
- Establishes the ports (canonical schema + results mart) that future adapters (real CDW
  input, Superset output, graph semantic layer) plug into without touching the domain.
