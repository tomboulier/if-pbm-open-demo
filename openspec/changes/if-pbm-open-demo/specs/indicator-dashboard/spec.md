## ADDED Requirements

### Requirement: Dashboard renders indicator trends
The system SHALL provide a Streamlit dashboard that visualizes each indicator's trend over
periods, with the ability to compare or filter by specialty. Dashboards, not tables, are the
primary output.

#### Scenario: Trends are displayed
- **WHEN** a user opens the dashboard
- **THEN** they see IR1-IR5 plotted over periods for orthopedics, cardiology, and gynecology

### Requirement: Dashboard reads only the results mart
The dashboard SHALL consume only the `indicator_results` mart and SHALL NOT query source
tables or depend on the compute engine, so that an alternative output adapter (e.g. Superset)
can read the same mart without changes to computation.

#### Scenario: Output adapter is decoupled
- **WHEN** the dashboard renders
- **THEN** it reads exclusively from the mart
- **AND** swapping the dashboard for another BI tool requires no change to data generation or indicators

### Requirement: Clone-and-run experience
The demo SHALL run from a fresh clone with a documented dependency install and a single
command that generates data, computes indicators, and launches the dashboard, without
requiring an external server.

#### Scenario: One-command run
- **WHEN** a new user installs dependencies and runs the documented command
- **THEN** synthetic data is generated, indicators are computed, and the dashboard becomes available
