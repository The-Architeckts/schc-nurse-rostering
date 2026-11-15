# Errata and post-submission notes

`SCHC_NRP_Dissertation.pdf` is the dissertation exactly as submitted and assessed in May 2026,
and it is left unchanged. After submission, its figures were checked against the final raw
results and code in this repository (`results/raw/`, `results/analysis/`). Where the two
disagree, **the results and code in this repository are authoritative**, and the corrections
are listed below.

All corrections can be checked with the scripts named in each item.

---

## 1. Number of instances used in the penalty validation (Section 4.4)

The text states that the penalty function was validated on "six representative instances".
It was validated on **seven**: sprint01 to sprint05, medium01 and long05
(`experiments/validate_penalty.py`, solution files in `data/toffolo_bks/`).

| Instance | Published | This evaluator | Difference |
|---|---|---|---|
| sprint01 | 56 | 56 | 0 |
| sprint02 | 58 | 57 | -1 |
| sprint03 | 51 | 51 | 0 |
| sprint04 | 59 | 58 | -1 |
| sprint05 | 58 | 55 | -3 |
| medium01 | 240 | 240 | 0 |
| long05 | 284 | 277 | -7 |

The other statements in that paragraph hold for the seven instances: discrepancies range from
0 to 7 points, all in the direction of under-penalisation; two Sprint instances and one Medium
instance agree exactly; and the mean absolute discrepancy is 1.6 percent of the published
penalty (below the 2.5 percent stated).

## 2. Missing column in Table 4.1

For SCHC-all and SCHC-acp at Sprint scale, Table 4.1 omits the Lc = 1000 results:

| Algorithm | Lc = 1000 mean penalty |
|---|---|
| SCHC-all | 58.86 |
| SCHC-acp | 56.10 |

They do not change the optimal Lc. Source: `results/analysis/summary_table.csv`.

## 3. Definition of the effect size r (Table 4.4)

The caption of Table 4.4 describes r as the matched-pairs rank-biserial correlation. The
values reported were computed as r = |Z| / √N, where Z is recovered from the two-sided
Wilcoxon p-value through the normal approximation (`experiments/analyse_results.py`,
function `wilcoxon_test`). The reported numbers are correct for that definition; only the
description is wrong. The two measures are related but not identical, so the values should not
be compared directly with rank-biserial correlations reported elsewhere.

## 4. Best results in Table 4.5

Five of the ten "This study (best)" values in Table 4.5 do not match the final results. The
correct values (minimum final penalty over all SCHC runs on that instance) are:

| Instance | Table 4.5 | Final results | BKS |
|---|---|---|---|
| Sprint01 | 54 | **53** | 56 |
| Sprint02 | 55 | 55 | 58 |
| Sprint03 | 50 | 50 | 51 |
| Sprint04 | 57 | 57 | 59 |
| Sprint05 | 54 | 54 | 58 |
| long01 | 179 | 179 | 197 |
| long02 | 205 | **202** | 226 |
| long03 | 220 | **213** | 240 |
| long04 | 270 | **283** | 303 |
| long05 | 251 | **264** | 284 |

The long04 and long05 values in the dissertation are lower than any result in the final data
and most likely come from earlier runs made with the pre-correction code, which were excluded
from the final analysis. Source: `results/raw/`, via this query on `results/schc_results.db`:

```sql
SELECT i.name, MIN(r.final_penalty) AS best
FROM runs r JOIN instances i USING (instance_id) JOIN algorithms a USING (algorithm_id)
WHERE a.name <> 'HC' AND i.name IN ('sprint01','sprint02','sprint03','sprint04','sprint05',
                                     'long01','long02','long03','long04','long05')
GROUP BY i.name;
```

## 5. Interpretation of comparisons with published results (Section 4.4)

Table 4.5 shows that the best results of this study are **below the published best-known
solution on every one of the ten instances**, by up to 27 points (long03). Taken at face value,
this would mean a simple local search in Python improved on the best results in the literature
for a heavily studied benchmark, which is not credible. (The only Medium instance with a
best-known value in the database, medium01, is the exception: the best result there is 245,
5 points above the published 240.) A far more likely explanation is that
the evaluator under-penalises the solutions found in this study by more than it under-penalises
the published solutions.

This is consistent with how optimisation works: each algorithm minimises the penalty as this
evaluator computes it, so it is drawn towards solutions that exploit whatever violations the
evaluator misses. The validation in item 1 measures the evaluator's error on *published*
solutions, which were not optimised against it, and so it does not bound the error on the
solutions found here. On sprint01, for example, the evaluator agrees exactly with the published
value of 56 for the best-known solution, yet this study's best solution scores 53.

Consequences:

* **Comparisons between HC and the SCHC variants are unaffected**, because all of them are
  scored by the same evaluator. All the conclusions about relative performance, Lc sensitivity
  and statistical significance stand.
* **Absolute penalties, and comparisons with other published methods (Table 4.5 and the
  surrounding discussion), should not be relied on.** The statements that SCHC is competitive
  with or better than HHSA at Sprint and Long scale are not supported.

A definitive check would be to export this study's best solutions in the INRC-I XML format and
score them with the official competition validator. That has not yet been done.
