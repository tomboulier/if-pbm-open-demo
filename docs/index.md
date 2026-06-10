# If-PBM Open Platform

Reproducible, open-source platform around the If-PBM Patient Blood Management
monitoring method (MIE2026 short communication, Grenoble Alpes University Hospital).

A synthetic clinical data warehouse, calibrated on the real aggregated If-PBM bilan,
feeds three surfaces:

- **Dashboards** generated automatically from the indicator registry (IR1-IR5 by
  specialty and trimester, with the year-2 targets of the cahier des charges).
- **Calibration**: the official real aggregated values overlaid on the synthetic
  pipeline, making the known-ground-truth claim visible.
- **Learn**: a self-correcting SQL training track on the warehouse, validated against
  the ground truth.

## Quick start

```bash
uv tool install git+https://github.com/tomboulier/if-pbm-open-demo
if-pbm-demo demo
```

## Indicators

| Indicator | Definition |
|-----------|------------|
| IR1 | Proportion of standardized PBM preoperative check-ups |
| IR2 | Proportion of corrective treatments for anemia / iron deficiency |
| IR3 | Proportion of single-unit transfusion episodes |
| IR4 | Proportion of patients transfused per- or post-operatively |
| IR5 | Proportion of patients discharged with low hemoglobin |

## Architecture

The method is decoupled behind two seams: a canonical input schema and an
`indicator_results` output mart, so data sources and dashboards are swappable. The
indicator **registry** is the single source of truth for definitions, targets, and SQL;
dashboards and exercise validation derive from it. See the
[README](https://github.com/tomboulier/if-pbm-open-demo) and the
[platform plan](platform-plan.md) for details.
