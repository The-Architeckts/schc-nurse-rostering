# Testing and continuous integration

This project's main claim is quantitative: a set of numbers produced by about 390 CPU-hours of
experiments. The tests are therefore designed to answer one question: **can every number this
repository reports be traced back to the code and the raw data, and would a change that broke
that link be noticed?**

Run them with:

```bash
pip install -r requirements.txt
python -m pytest
```

They take about ten seconds. The same command runs automatically on GitHub for every push and
pull request (`.github/workflows/ci.yml`).

## What is tested

### 1. Algorithm and penalty function (`tests/test_core.py`)

| Test | What it protects against |
|---|---|
| Greedy baseline is feasible and scores 254 on sprint01 | A change to the constructor or constraint code silently altering the starting point of every run |
| An empty roster is penalised by at least 10<sup>6</sup> | Hard constraint violations no longer dominating the objective |
| Published best-known solutions score as expected | Drift in the penalty function away from the validated version |
| HC and SCHC-all reproduce two Falcon runs exactly from their seeds | Any change to the search code that would make the published results irreproducible |

The last two are *regression tests*: they pin current, validated behaviour so that an
unintended change shows up as a failure. The reproduction tests are the strongest check in the
suite, because matching the final penalty, iteration count and bound updates of a run performed
months earlier on a different machine requires the code path to be identical.

### 2. Database and SQL (`tests/test_database.py`)

The database is rebuilt from the raw CSVs into a temporary folder for every test run.

* **Integrity checks:** all 2,800 runs and 20 instances are loaded, every configuration has
  exactly 10 seeds, HC rows have no Lc, and the schema rejects a duplicate run.
* **Cross-validation:** the three SQL queries are compared with the independent pandas and SciPy
  analysis in `results/analysis/`. Two separate implementations computing the same statistics
  must agree, which guards against a mistake in either one.

### 3. End-to-end reproducibility (`tests/test_pipeline.py`)

* The statistical analysis is rerun from `results/raw/` and every committed table and the text
  report must match it.
* The dashboard is regenerated from a freshly built database and must be identical to
  `docs/index.html`.

These catch outputs that have gone stale: for example, raw data or analysis code that was
changed without regenerating the published results.

## Does it catch real problems?

A test suite is only useful if it fails when something is wrong. As a check, the final penalty of
a single run (long03, HC, seed 4) was changed by one point. Seven tests failed: the cross-check
between the SQL and the pandas analysis, all five analysis reproducibility tests, and the
dashboard freshness test.

## What is not tested

* Full experiment runs. One instance takes hours, so CI checks reproduction on two short runs
  rather than rerunning the sweep.
* The figures in `results/figures/`. CI runs the plotting script to confirm it works but does
  not compare images.
* The scripts in `archive/`, which are kept for the record only.
