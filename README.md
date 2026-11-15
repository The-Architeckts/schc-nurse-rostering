# Step Counting Hill Climbing for the Nurse Rostering Problem

BSc (Hons) Computer Science dissertation, Bangor University, 2026. Awarded a First.
Supervisor: Dr Mosab Bazargani.

This repository contains the implementation, experimental pipeline, raw results, statistical
analysis and full write-up of a study applying the Step Counting Hill Climbing algorithm
(SCHC; Bykov and Petrovic, 2016) to the First International Nurse Rostering Competition
benchmark (INRC-I). It provides the first systematic evaluation of all three SCHC variants
on this benchmark.

**Full dissertation:** [`dissertation/SCHC_NRP_Dissertation.pdf`](dissertation/SCHC_NRP_Dissertation.pdf)

---

## Headline findings

The three SCHC variants were compared against a Hill Climbing (HC) baseline on all 20 INRC-I
early instances (10 Sprint, 5 Medium, 5 Long), with a sweep over the step counter limit
Lc and 10 seeded runs per configuration. In total, 2,800 runs were performed, consuming
approximately 390 CPU-hours on the Supercomputing Wales Falcon cluster.

1. **All three SCHC variants significantly outperform Hill Climbing at every scale**, reducing
   mean penalty by 9.5 to 20.6 percent (Wilcoxon signed-rank, p < 0.001, effect size r > 0.84
   in every case).
2. **SCHC-acp is the most consistently effective variant.** It is best at Long scale and
   statistically equivalent to SCHC-imp at Medium scale (p = 0.27).
3. **SCHC-imp is best at Sprint scale**, and its optimal Lc is approximately scale-invariant
   (25 at Sprint, 15 at Medium and Long). The optimal Lc of SCHC-all and SCHC-acp instead
   grows with problem size (1500 to 2500).
4. **The scale-invariance of SCHC-imp is explained by the NRP landscape.** Improving moves make
   up roughly 1 percent of iterations, so the SCHC-imp counter advances slowly and its
   effective bound-update frequency decouples from the nominal Lc. As improving moves become
   rarer at Long scale, SCHC-imp falls back to statistical equivalence with SCHC-all
   (p = 0.92).

![Mean penalty reduction relative to HC](results/figures/improvement_over_hc.png)

![Mean penalty against Lc for each variant and scale](results/figures/lc_sensitivity.png)

### Results at the optimal Lc

Mean final penalty over all instances and runs at each scale (lower is better).

| Scale | HC | SCHC-all | SCHC-acp | SCHC-imp |
|---|---|---|---|---|
| Sprint (10 instances × 10 runs) | 63.40 | 57.38 (Lc 1500) | 55.24 (Lc 1500) | **54.41** (Lc 25) |
| Medium (5 × 10) | 304.86 | 265.16 (Lc 2500) | **260.04** (Lc 2500) | 260.52 (Lc 15) |
| Long (5 × 10) | 292.88 | 238.88 (Lc 2500) | **232.46** (Lc 2500) | 238.62 (Lc 15) |

Pairwise comparisons between variants (Wilcoxon signed-rank at optimal Lc):

| Scale | acp vs all | imp vs all | imp vs acp |
|---|---|---|---|
| Sprint | acp better, p < 0.001 | imp better, p < 0.001 | imp better, p < 0.001 |
| Medium | acp better, p < 0.001 | imp better, p < 0.001 | not significant, p = 0.27 |
| Long | acp better, p < 0.001 | not significant, p = 0.92 | acp better, p < 0.001 |

The full tables are in [`results/analysis/`](results/analysis/), and the report printed by
the analysis script is [`results/analysis/analysis_report.txt`](results/analysis/analysis_report.txt).

---

## The algorithm

SCHC is a single-parameter local search. It keeps a cost bound and accepts any candidate
whose penalty is strictly below that bound. Every Lc counted steps, the bound is reset to the
current penalty. The variants differ only in what is counted:

| Variant | Counter advances on |
|---|---|
| SCHC-all | every iteration |
| SCHC-acp | every accepted move |
| SCHC-imp | every improving move |

Termination rules (all empirically calibrated, see Section 3.6 of the dissertation):

* **HC:** stop after 2,000 consecutive non-improving iterations.
* **SCHC-all and SCHC-acp:** stop when the idle counter exceeds 100 and also exceeds 1 percent
  of total iterations. The idle counter resets on any accepted move.
* **SCHC-imp:** stop when no new best solution has been found for max(30000, 500 × Lc)
  iterations. The adaptive rule above cannot fire for SCHC-imp on the NRP, because rare bound
  updates keep the bound high, so non-improving moves keep being accepted and the idle
  counter keeps resetting.

The search starts from a feasible greedy construction and uses six swap-based neighbourhood
operators that preserve feasibility. Hard constraints (coverage and one shift per nurse per
day) are penalised at 10<sup>6</sup> per violation; the seven INRC-I soft constraint types
(counters, series, patterns, complete and identical weekends, shift-off and day-off requests)
make up the objective.

---

## Repository layout

```
├── dissertation/            Full dissertation (PDF)
├── src/                     Final implementation
│   ├── models.py            Nurse, contract and shift type definitions
│   ├── data_loader.py       INRC-I JSON instance loader
│   ├── solution.py          2D nurse × day solution representation
│   ├── constructors.py      Greedy feasible baseline constructor
│   ├── constraints.py       Hard and soft constraint evaluation (penalty function)
│   ├── operators.py         Neighbourhood operators
│   └── algorithms/
│       ├── hill_climbing.py
│       └── schc.py          SCHC with all three variants
├── experiments/
│   ├── run_instance_sweep.py    Runs HC + all SCHC variants over the Lc sweep for one instance
│   ├── slurm/                   Slurm job arrays used on Falcon (sprint, medium, long)
│   ├── analyse_results.py       Descriptive statistics and Wilcoxon tests
│   ├── plot_results.py          Figures shown above
│   ├── validate_penalty.py      Checks the penalty function against published best-known solutions
│   ├── generate_per_instance_table.py   Per-instance LaTeX table used in the dissertation
│   └── pre_sweep_validation.py  Verbose single-instance run used to check variant behaviour
├── results/
│   ├── raw/                 Per-instance results.csv and checkpoint logs from Falcon (2,800 runs)
│   ├── analysis/            Output of analyse_results.py
│   └── figures/
├── data/
│   ├── inrc1/               INRC-I instances (JSON)
│   └── toffolo_bks/         Best-known solutions used for penalty validation
├── tests/                   Regression tests
└── archive/                 Earlier development work, kept for the record (see below)
```

---

## Reproducing the results

Python 3.12 is required. The algorithms use only the standard library; the analysis and
figures need the packages in `requirements.txt`.

```bash
pip install -r requirements.txt
```

**Quick checks (seconds):**

```bash
python -m pytest tests/                 # includes exact reproduction of two Falcon runs
python experiments/validate_penalty.py  # penalty function vs published best-known solutions
python experiments/analyse_results.py   # regenerates results/analysis/ from results/raw/
python experiments/plot_results.py      # regenerates results/figures/
```

`analyse_results.py` reproduces every table in `results/analysis/` exactly from the raw CSVs.

**Rerunning the experiments.** Every run is seeded with its run number, and the code in
`src/` is the code that ran on Falcon, so rerunning an instance regenerates its row of
`results/raw/` exactly (apart from the wall-clock times). One instance at a time:

```bash
python experiments/run_instance_sweep.py sprint 1    # roughly 2.5 hours on one core
```

The full experiment is three Slurm job arrays, one task per instance:

```bash
sbatch experiments/slurm/submit_sprint_array.sh   # 10 tasks, about 2.5 h each
sbatch experiments/slurm/submit_medium_array.sh   # 5 tasks, about 20 h each
sbatch experiments/slurm/submit_long_array.sh     # 5 tasks, about 50 to 58 h each
```

Set `--account` in each script to your own project before submitting. On a single machine
the whole sweep would take around 390 CPU-hours, so a cluster, or a lot of patience, is
recommended.

---

## Validity notes and limitations

* **Penalty function.** Evaluating the published best-known solutions of Toffolo et al. with
  this project's evaluator gives discrepancies of 0 to 7 points, always in the direction of
  under-penalisation (`experiments/validate_penalty.py`). Absolute penalties are therefore
  marginally optimistic; comparisons between algorithms are unaffected because they share the
  same evaluator.
* **Lc range.** For SCHC-all and SCHC-acp, the best Lc found at every scale is the largest
  value tested (1500 at Sprint, 2500 at Medium and Long), and the curves above are still
  falling there. Larger Lc may
  give further gains at proportionally higher cost; the reported optimum is the best value
  within the tested range.
* **Statistics.** Comparisons pair runs by instance and seed. The effect size r is derived
  from the normal approximation of the Wilcoxon p-value, as r = |Z| / √N.
* **Comparison with published methods** (Section 4.4 of the dissertation) is indicative only,
  as the reference results used different hardware and time budgets.

---

## Project history

Only the work described above reflects the final results. The project went through several
earlier stages, including results produced by implementations of the SCHC variants that were
later found to be incorrect. That material is kept in [`archive/`](archive/), together with a
timeline of how the work developed.

> **The conference-style poster in `archive/poster/` (March 2026) reports findings that were
> later disproven.** It was produced from the earlier, flawed implementation and does not
> reflect the final results. Please refer to this README and the dissertation instead.

The first 16 commits in this repository's history are the original development commits from
February 2026. The final experiments were run on the Falcon HPC cluster from April 2026 and
were added to version control after the project was completed.

---

## Citation

```
Armstrong, A. (2026). Step Counting Hill Climbing: Application to the Nurse Rostering
Problem. BSc dissertation, School of Computer Science and Electronic Engineering,
Bangor University.
```

## Acknowledgements

Supervised by Dr Mosab Bazargani. The Medium and Long experiments were made possible by
Supercomputing Wales and the Cardiff University Falcon HPC cluster, funded by the European
Regional Development Fund and the Welsh Government.

INRC-I instances: Haspeslagh, De Causmaecker, Schaerf and Stølevik (2014), *The first
international nurse rostering competition 2010*, Annals of Operations Research 218(1).
Best-known solutions: Toffolo et al., <https://benchmark.gent.cs.kuleuven.be/nrp>.

## Licence

The source code is released under the MIT Licence (see [`LICENSE`](LICENSE)). The
dissertation and poster are © Arthur Armstrong and are included for reading and reference;
please cite them if you use their content.
