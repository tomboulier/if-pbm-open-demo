## 1. Project scaffold and contract

- [x] 1.1 Create Python project scaffold (pyproject, src layout, README, CI/CD, instructions files)
- [x] 1.2 Add dependencies: duckdb, streamlit, pandas, numpy, plotly
- [x] 1.3 Define the canonical schema (patient, surgery, transfusion, lab, consultation) with keys
- [x] 1.4 Define the `indicator_results` mart shape (indicator, specialty, period, numerator, denominator, proportion)
- [x] 1.5 Add a `period` reporting-calendar dimension (rolling trimesters, joined by date range)

## 2. Synthetic data generation (input adapter, calibrated to the real bilan)

- [x] 2.1 Extract aggregated targets from bilan_if_pbm_full.xlsx into a shareable `data/targets.csv`
- [x] 2.2 Implement a seeded, target-driven generator emitting the canonical tables
- [x] 2.3 Construct patient-level rows so aggregation reproduces the per-specialty, per-trimester counts
- [x] 2.4 Verify reproduction against the bilan (exact counts for IR1-IR5 in tests)

## 3. Indicators (domain, as SQL over the canonical schema)

- [x] 3.1 IR1 preop check-up; IR2 anemia/iron correction
- [x] 3.2 IR3 single-unit episodes (1-hour episode windowing), internal-doc numbering
- [x] 3.3 IR4 transfused per/post-op (30-day censoring)
- [x] 3.4 IR5 low-Hb discharge
- [x] 3.6 Stratify all by specialty and period; materialize the `indicator_results` mart

## 4. Dashboard (output adapter)

- [x] 4.1 Streamlit app reading ONLY the mart
- [x] 4.2 Trend charts per indicator over periods, filter/compare by specialty
- [x] 4.3 Verify the dashboard never touches source tables (seam holds)

## 5. Clone-and-run + presentation readiness

- [x] 5.1 Single command: generate data -> compute indicators -> launch dashboard (`if-pbm-demo demo`)
- [x] 5.2 README: what it is, one-command run, link to MIE2026 paper, note on synthetic data
- [x] 5.3 Smoke test (pytest + headless dashboard boot); ruff + mypy green
- [ ] 5.4 Make repo public; add link/QR for the presentation  (owner action)

## 6. Parked (future "plus", do not build tonight)

- [ ] 6.1 Superset output adapter reading the same mart (for D2H)
- [ ] 6.2 Real-CDW input adapter conforming to the canonical schema
- [ ] 6.3 Graph / knowledge-layer view as a semantic layer (ArangoDB or networkx) + one example query
