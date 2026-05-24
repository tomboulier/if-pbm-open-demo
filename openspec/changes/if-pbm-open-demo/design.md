## Context

The production If-PBM pipeline at Grenoble (Easily/CNET/Diane/STARE/CURSUS -> 10 Talend jobs
-> JSON -> ArangoDB -> AQL queries -> 5 indicators) is faithful to the published method but
unshareable and unreproducible. The next regional CDW, D2H (DataHub Hourra: Grenoble, Lyon,
Saint-Etienne, Clermont-Ferrand), will use Superset for BI.

We are building an open demo under a hard deadline (presentation day). The owner's view:
the graph database is a funding differentiator and a promising *semantic layer* for future
LLM-based querying, but it is **not** the headline. The headline is that the method **works
end to end** and could be adopted by another center. SQL is preferred over AQL: portable,
LLM-friendly (text-to-SQL), and the natural substrate for a future knowledge-graph semantic
layer rather than a competitor to it.

## Goals / Non-Goals

**Goals:**
- One-command, clone-and-run demo from a public repo; no server, runs in seconds.
- Faithful reproduction of the five PBM indicators across 3 specialties and ~9 quarters.
- Synthetic data convincing enough to show plausible, specialty-differentiated trends.
- Input/output agnosticism *by construction*, via two stable seams, without DI ceremony.
- Dashboards (Streamlit) as the primary output, not tables.

**Non-Goals:**
- A Superset adapter (D2H is not here yet; the mart makes it a later half-day add).
- A real-CDW input adapter or any connection to hospital systems.
- An ArangoDB/AQL graph layer (optional future "plus", parked as semantic layer).
- A full hexagonal/clean-architecture framework or dependency-injection container.

## Decisions

### D1. Ports-as-tables, not interfaces
In a data system the useful "port" is a data contract, not a class. We define exactly two seams:
- **Input port = a canonical schema** (`patient`, `surgery`, `transfusion`, `lab`,
  `consultation`). Every source's only job is to produce conforming rows.
- **Output port = the `indicator_results` mart** (one stable table: indicator x specialty x
  quarter x value/numerator/denominator). Any BI tool reads it.

```
 input adapters        canonical schema        domain (SQL)        results mart        output adapters
 synthetic (now) ─┐                                              ┌──────────────┐   ┌─ Streamlit (now)
 real CDW (later) ┼──▶ patient/surgery/    ──▶ IR1..IR5 SQL  ──▶ │ indicator_   │──▶┼─ Superset (D2H, later)
 D2H/Superset src ┘    transfusion/lab/         over canonical   │ results      │   └─ CSV/plot export
                       consultation                              └──────────────┘
                        ▲ swap inputs                               ▲ swap outputs
```

### D2. DuckDB as the engine, indicators as SQL
DuckDB: single `pip install`, no server, fast, reads CSV/parquet directly. Indicators become
readable SQL another center can repoint at its own canonical tables. Engine is itself
swappable (the SQL targets the canonical schema, not DuckDB internals).

### D3. Implement one adapter per side, define the contract for both
Resist abstracting things we have only one of. Build the synthetic input adapter and the
Streamlit output adapter; specify the canonical schema and the mart so the second adapter on
each side is a drop-in later. The second adapter is what would *prove* the seam; we defer it.

### D4. Synthetic generator calibrated to the real bilan (inverse construction)
The generator does NOT invent indicator values. We extract the real aggregated counts from
`bilan_if_pbm_full.xlsx` into a shareable `targets.csv` (aggregated => GDPR-safe), then
construct patient-level rows so that aggregating them reproduces those counts. The runtime
pipeline stays faithful to production (patient data -> aggregate -> indicators); we only
invert it once, offline, to fabricate a consistent population. Seeded for reproducibility.
A PoC: counts are reproduced closely, not necessarily to the unit.

### D6. Reporting period as an explicit calendar dimension
If-PBM reports on rolling three-month trimesters (e.g. May-Jul 2023) that straddle calendar
quarters. Deriving the period from `quarter(surgery_date)` would split a trimester in two, so
the period is a `period(period, start_date, end_date)` dimension joined by date range. The
mart and dashboard use `period`, not calendar quarter.

### D5. Indicator definitions (authoritative source: internal If-PBM documentation)
- IR1: proportion of standardized PBM preoperative check-ups (at pre-anesthesia consultation).
- IR2: proportion of corrective treatments for anemia or iron deficiency.
- IR3: proportion of single-unit transfusion episodes (episode = 1-hour window from the first
  red-blood-cell unit delivery).
- IR4: proportion of patients transfused per- or post-operatively.
- IR5: proportion of patients discharged with low hemoglobin.
Per/post-op events are censored at 30 days after surgery. Specialties: orthopedics,
cardiology, gynecology. Numbering follows the internal documentation (which defines IR3 as
single-unit episodes), not the MIE2026 abstract ordering.

## Risks / Trade-offs

- **Synthetic-data realism is the real risk**, not the indicators. If trends look random or
  implausible the demo undersells the method. Mitigation: D4 tunable adherence + drift, seeded;
  sanity-check against the directions in the real `ir*_tendance.png`.
- **SQL vs published AQL/graph** diverges from the paper's exact tooling. Mitigation: frame
  the graph as semantic-layer future work; the method (entities, linkage, indicator logic) is
  preserved, only the engine changes.
- **Deadline pressure** could tempt over-engineering. Mitigation: D3 hard limit of one adapter
  per side tonight.
- **Indicator numbering ambiguity** (IR3/IR4) between abstract and internal docs; flagged in D5
  for owner confirmation.
