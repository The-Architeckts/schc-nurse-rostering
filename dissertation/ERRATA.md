# Errata and post-submission notes

`SCHC_NRP_Dissertation.pdf` is the dissertation as submitted and assessed in May 2026. Its
content is unchanged; only the two signature images on the declarations page have been blanked
for public release. After submission, its results tables and principal quantitative statements
were checked against the final raw results and code in this repository
(`results/raw/`, `results/analysis/`). Where the two disagree, **the results and code in this
repository are authoritative**. The corrections are listed below, and all of them are applied
in the revised edition, [`SCHC_NRP_Dissertation_revised.pdf`](SCHC_NRP_Dissertation_revised.pdf)
(Appendix A of that edition lists them as well).

Each correction can be checked with the scripts or queries named in the item.

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

## 3. Statistical method (Chapter 1, Section 3.7.3, Section 4.3, Table 4.4)

The submitted text states that the Wilcoxon signed-rank tests were applied to paired
per-instance mean penalties (n = 10 at Sprint, n = 5 at Medium and Long), and that the effect
size r is the matched-pairs rank-biserial correlation. The analysis
(`experiments/analyse_results.py`) actually:

* applied the tests to **individual runs paired by instance and random seed**, giving
  N = 100 pairs at Sprint and N = 50 at Medium and Long; and
* computed **r = |Z| / √N**, with Z recovered from the two-sided p-value through the normal
  approximation (Fritz, Morris and Richler, 2012).

The reported statistics are correct for this method; only the description was wrong. The
original description was also internally inconsistent: with n = 5, a two-sided Wilcoxon test
cannot produce p < 0.05, yet p < 0.001 was reported at Medium and Long scale.

Because runs on the same instance are not fully independent, the reported p-values are likely
to overstate the strength of evidence compared with an analysis that treats instance as a
grouping factor (for example a mixed-effects model). The direction of every main effect is
consistent across individual instances, so the conclusions are not in doubt, but the p-values
should be read as indicative. The revised edition adds this as a limitation.

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

## 6. Description of the corrected implementation defect (Section 5.6.1)

The submitted text says the initial SCHC-imp idle counter "was incorrectly resetting on any
accepted move rather than exclusively on improving moves". This is the reverse of what the
code shows. In the final implementation (`src/algorithms/schc.py`), the idle counter is reset
by **any accepted move**, uniformly for all three variants; the correction made the tracking
uniform across variants.

## 7. Improving move rates (Section 5.3)

The submitted text gives improving move rates at Sprint scale of 1.06, 9.35 and 5.92 percent
for SCHC-imp, SCHC-all and SCHC-acp, and states that Lc = 25 for SCHC-imp corresponds to about
2,500 iterations per bound update. Across all final Sprint runs at optimal Lc, the rates are
**1.18, 9.02 and 5.70 percent**, and the measured iterations per bound update are **2,137** for
SCHC-imp (Lc = 25) and **1,515** for SCHC-all (Lc = 1500). The argument in that section is
unchanged by the corrected figures.

```sql
SELECT a.name, r.lc,
       ROUND(100.0 * SUM(improving_moves) / SUM(iterations), 2) AS improving_pct,
       ROUND(1.0 * SUM(iterations) / SUM(bound_updates), 0)     AS iters_per_update
FROM runs r JOIN instances i USING (instance_id) JOIN algorithms a USING (algorithm_id)
WHERE i.scale = 'sprint'
  AND ((a.name = 'SCHC-imp' AND r.lc = 25) OR (a.name IN ('SCHC-all', 'SCHC-acp') AND r.lc = 1500))
GROUP BY a.name, r.lc;
```

## 8. Citation of Bykov and Petrovic (2016)

The submitted bibliography gives the SCHC paper as *Journal of Scheduling* 19(1):55 to 71 with
DOI 10.1007/s10951-014-0391-z. The correct reference is *Journal of Scheduling* **19(4):479 to
492**, DOI **10.1007/s10951-016-0469-x**.

