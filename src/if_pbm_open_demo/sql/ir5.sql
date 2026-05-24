-- IR5: proportion of patients discharged with low hemoglobin.
-- The discharge hemoglobin is the last hemoglobin measured within 30 days after surgery.
-- Low is defined by the threshold injected as $low_hb (g/dL).
WITH discharge_hb AS (
    SELECT
        s.surgery_id,
        s.specialty,
        s.surgery_date,
        arg_max(l.value, l.sample_datetime) AS hb
    FROM surgery s
    JOIN lab l ON l.surgery_id = s.surgery_id
    WHERE l.test = 'hemoglobin'
      AND l.sample_datetime >= s.surgery_date
      AND l.sample_datetime < s.surgery_date + INTERVAL 30 DAY
    GROUP BY 1, 2, 3
)
SELECT
    d.specialty AS specialty,
    pd.period AS period,
    count(*) FILTER (WHERE d.hb < $low_hb) AS numerator,
    count(*) AS denominator
FROM discharge_hb d
JOIN period pd ON d.surgery_date BETWEEN pd.start_date AND pd.end_date
GROUP BY 1, 2
