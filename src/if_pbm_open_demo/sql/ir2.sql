-- IR2: proportion of corrective treatments for anemia / iron deficiency.
-- Denominator: surgeries where anemia / iron deficiency was detected at the consultation.
-- Numerator: those where a corrective treatment was given.
SELECT
    s.specialty AS specialty,
    pd.period AS period,
    count(*) FILTER (WHERE c.anemia_corrected) AS numerator,
    count(*) AS denominator
FROM surgery s
JOIN consultation c ON c.surgery_id = s.surgery_id
JOIN period pd ON s.surgery_date BETWEEN pd.start_date AND pd.end_date
WHERE c.anemia_detected
GROUP BY 1, 2
