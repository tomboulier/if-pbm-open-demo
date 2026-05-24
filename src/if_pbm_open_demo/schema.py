"""Canonical data contract and the indicator results mart.

These two artifacts are the only stable seams of the system:

- The **canonical schema** (``patient``, ``surgery``, ``transfusion``, ``lab``,
  ``consultation``) is the input port. Every data source's only job is to produce rows
  conforming to it; indicator computation depends on nothing else.
- The ``indicator_results`` **mart** is the output port. Any dashboard or BI tool reads
  only this table, never the source tables or the compute engine.
"""

from __future__ import annotations

#: Canonical entities, in dependency order (patients before anything referencing them).
CANONICAL_TABLES: tuple[str, ...] = (
    "patient",
    "surgery",
    "consultation",
    "lab",
    "transfusion",
)

#: DDL for the canonical schema (the input port / data contract).
CANONICAL_SCHEMA_SQL = """
CREATE TABLE patient (
    patient_id   BIGINT PRIMARY KEY,
    birth_year   INTEGER,
    sex          VARCHAR
);

CREATE TABLE surgery (
    surgery_id   BIGINT PRIMARY KEY,
    patient_id   BIGINT NOT NULL,
    specialty    VARCHAR NOT NULL,   -- orthopedics | cardiology | gynecology
    surgery_date DATE NOT NULL
);

CREATE TABLE consultation (
    consultation_id  BIGINT PRIMARY KEY,
    patient_id       BIGINT NOT NULL,
    surgery_id       BIGINT,         -- pre-anesthesia consultation matched to a surgery
    consultation_date DATE NOT NULL,
    pbm_checkup_done BOOLEAN NOT NULL,   -- IR1: standardized PBM preoperative check-up
    anemia_detected  BOOLEAN NOT NULL,   -- IR2 denominator eligibility
    anemia_corrected BOOLEAN NOT NULL    -- IR2 numerator
);

CREATE TABLE lab (
    lab_id          BIGINT PRIMARY KEY,
    patient_id      BIGINT NOT NULL,
    surgery_id      BIGINT,
    test            VARCHAR NOT NULL,    -- e.g. 'hemoglobin'
    value           DOUBLE,
    unit            VARCHAR,
    sample_datetime TIMESTAMP NOT NULL
);

CREATE TABLE transfusion (
    transfusion_id    BIGINT PRIMARY KEY,
    patient_id        BIGINT NOT NULL,
    surgery_id        BIGINT,
    product_type      VARCHAR NOT NULL,  -- 'RBC' for red blood cell units (CGR)
    delivery_datetime TIMESTAMP NOT NULL
);
"""

#: DDL for the reporting calendar dimension. If-PBM reports on rolling three-month
#: trimesters (e.g. May-Jul 2023) that do not align to calendar quarters, so the period
#: must be an explicit dimension joined by date range, not derived from the date.
PERIOD_SCHEMA_SQL = """
CREATE TABLE period (
    period     VARCHAR PRIMARY KEY,   -- e.g. '2023-T1'
    start_date DATE NOT NULL,
    end_date   DATE NOT NULL
);
"""

#: DDL for the output port: a self-contained results mart.
MART_SCHEMA_SQL = """
CREATE TABLE indicator_results (
    indicator   VARCHAR NOT NULL,   -- 'IR1' .. 'IR5'
    specialty   VARCHAR NOT NULL,
    period      VARCHAR NOT NULL,   -- e.g. '2023-T1'
    numerator   BIGINT NOT NULL,
    denominator BIGINT NOT NULL,
    proportion  DOUBLE              -- numerator / denominator, NULL if denominator = 0
);
"""

#: Hemoglobin threshold (g/dL) below which a discharge is considered "low Hb" (IR5).
LOW_HB_THRESHOLD_G_DL = 10.0
