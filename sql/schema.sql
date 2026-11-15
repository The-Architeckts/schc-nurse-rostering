-- Schema for the SCHC nurse rostering results database.
--
-- One row per optimisation run in `runs`, with instance and algorithm
-- details normalised into their own tables. Built by
-- experiments/build_database.py from results/raw/*/results.csv.

PRAGMA foreign_keys = ON;

CREATE TABLE instances (
    instance_id   INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL UNIQUE,          -- e.g. 'sprint01'
    scale         TEXT    NOT NULL CHECK (scale IN ('sprint', 'medium', 'long')),
    nurses        INTEGER NOT NULL CHECK (nurses > 0),
    days          INTEGER NOT NULL CHECK (days > 0),
    bks_penalty   INTEGER                           -- published best-known solution, where used
);

CREATE TABLE algorithms (
    algorithm_id  INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,             -- 'HC', 'SCHC-all', 'SCHC-acp', 'SCHC-imp'
    counter_rule  TEXT                              -- what advances the step counter (NULL for HC)
);

CREATE TABLE runs (
    run_id            INTEGER PRIMARY KEY,
    instance_id       INTEGER NOT NULL REFERENCES instances (instance_id),
    algorithm_id      INTEGER NOT NULL REFERENCES algorithms (algorithm_id),
    lc                INTEGER CHECK (lc IS NULL OR lc > 0),   -- NULL for HC
    seed              INTEGER NOT NULL CHECK (seed BETWEEN 1 AND 10),
    baseline_penalty  INTEGER NOT NULL,
    final_penalty     INTEGER NOT NULL CHECK (final_penalty <= baseline_penalty),
    iterations        INTEGER NOT NULL,
    improving_moves   INTEGER NOT NULL,
    bound_updates     INTEGER NOT NULL,
    elapsed_seconds   REAL    NOT NULL
);

-- One run per (instance, algorithm, Lc, seed). IFNULL makes HC rows,
-- which have no Lc, unique as well.
CREATE UNIQUE INDEX ux_runs_config
    ON runs (instance_id, algorithm_id, IFNULL(lc, 0), seed);

-- Mean result for every configuration, used by the queries and dashboard.
CREATE VIEW v_config_summary AS
SELECT
    i.scale,
    a.name                         AS algorithm,
    r.lc,
    COUNT(*)                       AS n_runs,
    AVG(r.final_penalty)           AS mean_penalty,
    MIN(r.final_penalty)           AS best_penalty,
    MAX(r.final_penalty)           AS worst_penalty,
    AVG(r.elapsed_seconds)         AS mean_seconds
FROM runs r
JOIN instances  i USING (instance_id)
JOIN algorithms a USING (algorithm_id)
GROUP BY i.scale, a.name, r.lc;
