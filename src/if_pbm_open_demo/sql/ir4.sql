-- IR4: proportion of patients transfused per- or post-operatively.
-- Denominator: all surgeries.
-- Numerator: surgeries with at least one red-blood-cell unit delivered within 30 days.
WITH transfused AS (
    SELECT
        s.surgery_id,
        s.specialty,
        s.surgery_date,
        EXISTS (
            SELECT 1
            FROM transfusion t
            WHERE t.surgery_id = s.surgery_id
              AND t.product_type = 'RBC'
              AND t.delivery_datetime >= s.surgery_date
              AND t.delivery_datetime < s.surgery_date + INTERVAL 30 DAY
        ) AS was_transfused
    FROM surgery s
)
SELECT
    tr.specialty AS specialty,
    pd.period AS period,
    count(*) FILTER (WHERE tr.was_transfused) AS numerator,
    count(*) AS denominator
FROM transfused tr
JOIN period pd ON tr.surgery_date BETWEEN pd.start_date AND pd.end_date
GROUP BY 1, 2
