-- Q2. Head to head against Hill Climbing: at its optimal Lc, how often does
-- each SCHC variant beat HC on the same instance with the same seed?
--
-- Each SCHC run is paired with the HC run on the same instance and seed,
-- the same pairing used by the Wilcoxon signed-rank tests.

WITH optimal AS (
    SELECT scale, algorithm, lc
    FROM (
        SELECT scale, algorithm, lc,
               RANK() OVER (PARTITION BY scale, algorithm ORDER BY mean_penalty) AS lc_rank
        FROM v_config_summary
        WHERE algorithm <> 'HC'
    )
    WHERE lc_rank = 1
),
schc AS (
    SELECT i.scale, a.name AS algorithm, r.instance_id, r.seed, r.final_penalty
    FROM runs r
    JOIN instances  i USING (instance_id)
    JOIN algorithms a USING (algorithm_id)
    JOIN optimal    o ON o.scale = i.scale AND o.algorithm = a.name AND o.lc = r.lc
),
hc AS (
    SELECT r.instance_id, r.seed, r.final_penalty
    FROM runs r
    JOIN algorithms a USING (algorithm_id)
    WHERE a.name = 'HC'
)
SELECT
    s.scale,
    s.algorithm,
    COUNT(*)                                                       AS paired_runs,
    SUM(s.final_penalty <  h.final_penalty)                        AS wins,
    SUM(s.final_penalty =  h.final_penalty)                        AS ties,
    SUM(s.final_penalty >  h.final_penalty)                        AS losses,
    ROUND(100.0 * SUM(s.final_penalty < h.final_penalty) / COUNT(*), 1) AS win_rate_pct,
    ROUND(AVG(h.final_penalty - s.final_penalty), 2)               AS mean_penalty_saved
FROM schc s
JOIN hc   h ON h.instance_id = s.instance_id AND h.seed = s.seed
GROUP BY s.scale, s.algorithm
ORDER BY CASE s.scale WHEN 'sprint' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
         s.algorithm;
