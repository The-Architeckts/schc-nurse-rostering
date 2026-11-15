-- Q1. Which Lc is optimal for each SCHC variant at each scale, and how
-- much does it improve on Hill Climbing?
--
-- The optimal Lc is the value with the lowest mean final penalty over all
-- instances and seeds at that scale. Matches results/analysis/optimal_lc_table.csv.

WITH ranked AS (
    SELECT
        scale,
        algorithm,
        lc,
        mean_penalty,
        RANK() OVER (PARTITION BY scale, algorithm ORDER BY mean_penalty) AS lc_rank
    FROM v_config_summary
    WHERE algorithm <> 'HC'
),
hc AS (
    SELECT scale, mean_penalty AS hc_mean
    FROM v_config_summary
    WHERE algorithm = 'HC'
)
SELECT
    r.scale,
    r.algorithm,
    r.lc                                                    AS optimal_lc,
    ROUND(r.mean_penalty, 2)                                AS mean_penalty,
    ROUND(hc.hc_mean, 2)                                    AS hc_mean_penalty,
    ROUND(100.0 * (hc.hc_mean - r.mean_penalty) / hc.hc_mean, 1) AS pct_reduction_vs_hc
FROM ranked r
JOIN hc USING (scale)
WHERE r.lc_rank = 1
ORDER BY CASE r.scale WHEN 'sprint' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
         r.algorithm;
