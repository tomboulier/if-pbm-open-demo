-- IR1: proportion of standardized PBM preoperative check-ups.
-- Denominator: surgeries with a pre-anesthesia consultation.
-- Numerator: those whose consultation recorded a standardized PBM check-up.
SELECT
    s.specialty AS specialty,
    pd.period AS period,
    count(*) FILTER (WHERE c.pbm_checkup_done) AS numerator,
    count(*) AS denominator
FROM surgery s
JOIN consultation c ON c.surgery_id = s.surgery_id
JOIN period pd ON s.surgery_date BETWEEN pd.start_date AND pd.end_date
GROUP BY 1, 2
