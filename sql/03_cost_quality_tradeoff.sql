-- Q3. What does each increase in Lc cost in run time, and what does it buy
-- in solution quality?
--
-- For each variant and scale, steps through the tested Lc values in order
-- and compares each with the previous one using LAG.

WITH steps AS (
    SELECT
        scale,
        algorithm,
        lc,
        mean_penalty,
        mean_seconds,
        LAG(mean_penalty) OVER w AS prev_penalty,
        LAG(mean_seconds) OVER w AS prev_seconds
    FROM v_config_summary
    WHERE algorithm <> 'HC'
    WINDOW w AS (PARTITION BY scale, algorithm ORDER BY lc)
)
SELECT
    scale,
    algorithm,
    lc,
    ROUND(mean_penalty, 2)                           AS mean_penalty,
    ROUND(mean_seconds, 1)                           AS mean_seconds_per_run,
    ROUND(prev_penalty - mean_penalty, 2)            AS penalty_gain_vs_prev_lc,
    ROUND(mean_seconds - prev_seconds, 1)            AS extra_seconds_vs_prev_lc,
    CASE
        WHEN prev_penalty IS NULL THEN NULL
        WHEN prev_penalty - mean_penalty <= 0 THEN NULL       -- no gain
        ELSE ROUND((mean_seconds - prev_seconds) / (prev_penalty - mean_penalty), 1)
    END                                              AS seconds_per_point_gained
FROM steps
ORDER BY CASE scale WHEN 'sprint' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
         algorithm, lc;
