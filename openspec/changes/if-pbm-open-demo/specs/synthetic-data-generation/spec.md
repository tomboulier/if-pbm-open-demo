## ADDED Requirements

### Requirement: Canonical clinical data contract
The system SHALL define a canonical schema that all data sources conform to, consisting of
the entities `patient`, `surgery`, `transfusion`, `lab`, and `consultation`, with explicit
keys linking transfusions, labs, and consultations to a patient and, where applicable, to a
surgery. Indicator computation SHALL depend only on this schema, never on a specific source.

#### Scenario: Generated data conforms to the contract
- **WHEN** the synthetic generator runs
- **THEN** it produces tables for each canonical entity with the contract's columns and keys
- **AND** every transfusion, lab, and consultation references an existing patient
- **AND** every surgery references an existing patient and carries a specialty label

### Requirement: Synthetic data covers the study scope
The generator SHALL produce records spanning the reporting trimesters covered by the bilan
(May 2023 onward) across the specialties orthopedics, cardiology, and gynecology, at volumes
matching the published cohort.

#### Scenario: Coverage across periods and specialties
- **WHEN** the generator runs with default settings
- **THEN** every reporting period contains surgeries for each of the three specialties

### Requirement: Calibration to the aggregated bilan
The generator SHALL be calibrated against the real, aggregated If-PBM bilan (shipped as a
shareable `targets.csv` of per-specialty, per-trimester counts). It SHALL construct
patient-level rows such that, once aggregated by the indicator SQL, the results reproduce
those published counts (closely; exact reproduction is not required). The generator SHALL NOT
invent indicator values. Generation SHALL be reproducible from a fixed random seed.

#### Scenario: Aggregation reproduces the bilan
- **WHEN** the synthetic data is generated and the indicators are computed
- **THEN** each (indicator, specialty, period) result matches the corresponding bilan target

#### Scenario: Reproducible output
- **WHEN** the generator runs twice with the same seed
- **THEN** it produces identical data
