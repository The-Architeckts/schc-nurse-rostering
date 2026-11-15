# Archive: development history

> **Nothing in this folder reflects the final results.** It is kept so that the development
> of the project can be followed. For the final implementation, results and conclusions, see
> the [main README](../README.md) and the [dissertation](../dissertation/SCHC_NRP_Dissertation.pdf).

Much of the material here was produced before two implementation problems in the SCHC
variants were identified and corrected (see April 2026 below). Results from before that
point are biased, in particular against SCHC-imp, and should not be cited. The scripts are
also not maintained: they assume the earlier repository layout and several of them will not
run against the final code without changes.

## Timeline

| Date (2026) | Stage | Material |
|---|---|---|
| 10 to 11 Feb | Data loading, solution representation, greedy constructor, hard and soft constraint evaluation, neighbourhood operators, Hill Climbing. | git history; `figures/hc_convergence.png` |
| 23 Feb | HC baseline on the 10 Sprint instances. | `outputs/hc_standard_*` |
| 23 to 24 Feb | First SCHC implementation (counting all moves) and a 400-run Sprint study. | `outputs/schc_batch_*`; `figures/schc_comparison.png` |
| 24 to 25 Feb | SCHC-acp and SCHC-imp added; first Medium experiments and Medium Lc sweep. | `outputs/schc_variants_*`, `outputs/medium_*` |
| 25 to 27 Feb | Support for Long instances (DH shift type); Long Lc sweep, including Lc = 5000; Sprint Lc sweep. | `outputs/long_*`, `outputs/sprint_lc_sweep_*` |
| 1 to 3 Mar | Medium Lc scaling runs and the project poster. | `outputs/medium_lc_scaling_*`; `poster/` |
| Mar to mid Apr | Diagnosis of the poor and erratic behaviour of SCHC-imp and correction of the variant implementations (below). First Falcon job scripts. | `scripts/overnight_test.py`, `scripts/run_instance_sweep_v1.py`, `scripts/slurm/` |
| 21 Apr | Overnight local validation of the corrected variants with variant-specific Lc ranges. | `outputs/overnight_*` |
| 24 to 29 Apr | Final experiments on the Falcon HPC cluster. | `../results/raw/` (final) |
| 4 May | Statistical analysis. | `../results/analysis/` (final) |
| May | Dissertation submitted. | `../dissertation/` (final) |

## What changed between the early and final implementations

Two problems were found in the early variant implementations.

1. **Termination.** Early SCHC runs stopped after a fixed number of idle iterations
   (10,000, later max(10000, 10 × Lc)), and in the variant implementation the idle counter
   was not tracked uniformly across the three variants. Run length, and therefore solution
   quality, depended on each variant's counting rule rather than on convergence, which
   disadvantaged SCHC-imp in particular. The final implementation resets the idle counter on
   any accepted move for every variant, uses the adaptive rule idle > 100 and idle > 1 percent
   of total iterations for SCHC-all and SCHC-acp, and uses a stagnation rule (no new best for
   max(30000, 500 × Lc) iterations) for SCHC-imp, for which the adaptive rule cannot fire on
   this problem.
2. **Lc ranges for SCHC-imp.** SCHC-imp was initially tested over the same Lc values as the
   other variants. Since its counter advances only on improving moves, those values gave it
   very few bound updates per run. The final experiments use a separate, much smaller range
   for SCHC-imp (15 to 100), which is where its optimum lies.

Earlier conclusions that did not survive these corrections include the claim that SCHC-acp
is insensitive to Lc at Sprint scale (in the final results its mean penalty falls from 73.9
at Lc = 100 to 55.2 at Lc = 1500), the explanation of variant behaviour in terms of
acceptance rate (the final account rests on the improving move rate), and the recommended
"Lc of about 1.0 times problem size". No statistical significance testing had been carried
out at that stage.

## Contents

| Folder | Contents |
|---|---|
| `poster/` | The March 2026 poster, its figures, and the script that generated them. **Outdated; see the warning in that folder.** |
| `outputs/` | Summary CSVs, logs and plots from the February to April experiments. Per-run trace files and plots from the two largest early batches were omitted. |
| `scripts/` | Early experiment drivers, ad hoc test scripts, the first Falcon runner and Slurm scripts, and a local monitoring script. |
| `figures/` | Early HC and SCHC convergence plots. |
