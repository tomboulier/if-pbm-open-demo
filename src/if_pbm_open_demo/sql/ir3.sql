-- IR3: proportion of single-unit transfusion episodes.
-- A transfusion episode is a run of red-blood-cell units delivered less than one hour
-- apart (the first unit opens the episode). An episode is single-unit if it has one unit.
-- Per/post-operative units are censored at 30 days after surgery.
WITH rbc AS (
    SELECT
        t.surgery_id,
        s.specialty,
        s.surgery_date,
        t.delivery_datetime
    FROM transfusion t
    JOIN surgery s ON s.surgery_id = t.surgery_id
    WHERE t.product_type = 'RBC'
      AND t.delivery_datetime >= s.surgery_date
      AND t.delivery_datetime < s.surgery_date + INTERVAL 30 DAY
),
flagged AS (
    SELECT
        surgery_id,
        specialty,
        surgery_date,
        delivery_datetime,
        CASE
            WHEN lag(delivery_datetime) OVER w IS NULL
                 OR delivery_datetime - lag(delivery_datetime) OVER w > INTERVAL 1 HOUR
            THEN 1 ELSE 0
        END AS opens_episode
    FROM rbc
    WINDOW w AS (PARTITION BY surgery_id ORDER BY delivery_datetime)
),
episodes AS (
    SELECT
        surgery_id,
        specialty,
        surgery_date,
        sum(opens_episode) OVER (
            PARTITION BY surgery_id ORDER BY delivery_datetime
        ) AS episode_no
    FROM flagged
),
episode_sizes AS (
    SELECT
        surgery_id,
        specialty,
        surgery_date,
        episode_no,
        count(*) AS n_units
    FROM episodes
    GROUP BY 1, 2, 3, 4
)
SELECT
    es.specialty AS specialty,
    pd.period AS period,
    count(*) FILTER (WHERE es.n_units = 1) AS numerator,
    count(*) AS denominator
FROM episode_sizes es
JOIN period pd ON es.surgery_date BETWEEN pd.start_date AND pd.end_date
GROUP BY 1, 2
