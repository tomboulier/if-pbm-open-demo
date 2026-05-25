# If-PBM Open Demo

Reproducible, open-source demo of the If-PBM Patient Blood Management monitoring method
(MIE2026 short communication, Grenoble Alpes University Hospital).

It generates synthetic clinical data, computes the five If-PBM indicators (IR1-IR5) by
specialty and trimester, and serves an interactive dashboard. All data is synthetic.

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
`indicator_results` output mart, so data sources and dashboards are swappable. See the
[README](https://github.com/tomboulier/if-pbm-open-demo) for details.
