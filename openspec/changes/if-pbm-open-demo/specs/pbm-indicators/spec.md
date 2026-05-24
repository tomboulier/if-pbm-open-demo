## ADDED Requirements

### Requirement: Compute the five PBM indicators
The system SHALL compute the five If-PBM indicators over the canonical schema using SQL:
- IR1: proportion of standardized PBM preoperative check-ups (at pre-anesthesia consultation);
- IR2: proportion of corrective treatments for anemia or iron deficiency;
- IR3: proportion of single-unit transfusion episodes (episode = a 1-hour window starting at
  the first red-blood-cell unit delivery);
- IR4: proportion of patients transfused per- or post-operatively;
- IR5: proportion of patients discharged with low hemoglobin.
Per/post-operative events SHALL be censored at 30 days after surgery.

#### Scenario: All five indicators are produced
- **WHEN** the indicator computation runs over conforming canonical data
- **THEN** it returns a value for each of IR1 through IR5

#### Scenario: Transfusion episode windowing
- **WHEN** a patient receives multiple red-blood-cell units within one hour of the first unit
- **THEN** those units count as a single transfusion episode for IR3

### Requirement: Stratification by specialty and period
Each indicator SHALL be computed independently for orthopedics, cardiology, and gynecology,
and for each reporting period. Because If-PBM periods are rolling trimesters that do not
align to calendar quarters, the period SHALL be assigned by joining the surgery date to an
explicit reporting-calendar dimension, not derived from the date.

#### Scenario: Per-stratum results
- **WHEN** computation runs
- **THEN** each (indicator, specialty, period) combination yields its own value

### Requirement: Results materialized to a stable mart
The system SHALL materialize results into an `indicator_results` mart keyed by indicator,
specialty, and period, exposing at least the numerator, denominator, and proportion. This
mart is the sole contract between computation and any output adapter; consumers SHALL NOT
depend on the compute engine or storage internals.

#### Scenario: Mart is self-contained
- **WHEN** the mart is produced
- **THEN** each row carries indicator, specialty, period, numerator, denominator, and proportion
- **AND** a consumer can render results using only the mart, with no access to source tables
