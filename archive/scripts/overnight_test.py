'''
Overnight Validation Test - Variant-Specific Lc Sweep
======================================================
Tests all three SCHC variants across problem scales with Lc ranges
calibrated to each variant's counting mechanism.

Key finding driving this design:
    SCHC-imp on the NRP counts only improving moves (~1-10% of iters),
    so equivalent bound update frequency requires Lc_imp << Lc_all/acp.
    The hypothesis Lc_imp_opt ≈ Lc_all_opt × r_0 (where r_0 is the
    initial improving move rate, ~9%) predicts optimal Lc_imp ≈ 45-50
    for medium instances where Lc_all_opt ≈ 500.

    This test validates that hypothesis across sprint and medium scales
    and gathers the data needed to formulate the optimal Lc relationship.

DESIGN:
    Sprint (10 instances, 3 runs per config):
        HC baseline
        SCHC-all:  Lc in [100, 150, 250, 500, 1000]
        SCHC-acp:  Lc in [100, 150, 250, 500, 1000]
        SCHC-imp:  Lc in [25, 50, 80, 100, 150]

    Medium (3 instances: 01, 03, 05 for variety, 3 runs per config):
        HC baseline
        SCHC-all:  Lc in [500, 1000, 1500, 2500]
        SCHC-acp:  Lc in [500, 1000, 1500, 2500]
        SCHC-imp:  Lc in [25, 50, 80, 100]

ESTIMATED RUNTIME:
    Sprint all/acp:   ~1.5 hours
    Sprint imp:       ~3-4 hours  (slower per run, stagnation terminates)
    Medium all/acp:   ~3-4 hours
    Total:            ~8-9 hours

TERMINATION:
    SCHC-all / SCHC-acp: adaptive per Burke & Bykov (idle > 0.01 * total)
    SCHC-imp: stagnation (no new best for max(30000, Lc*500) iters)

OUTPUT:
    outputs/overnight_<TIMESTAMP>/
        results.csv         - all run records
        checkpoint.txt      - progress log
        sprint_summary.txt  - sprint analysis
        medium_summary.txt  - medium analysis
'''

import sys
from pathlib import Path
import time
import csv
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.hill_climbing import HillClimbing
from algorithms.schc import SCHC
from constraints import evaluate_solution

# ============================================================================
# CONFIGURATION
# ============================================================================

SPRINT_INSTANCES = [
    f'data/inrc1/INRC1_sprint{i:02d}.json' for i in range(1, 11)
]

MEDIUM_INSTANCES = [
    'data/inrc1/INRC1_medium01.json',
    'data/inrc1/INRC1_medium03.json',
    'data/inrc1/INRC1_medium05.json',
]

# Variant-specific Lc ranges
SPRINT_LC = {
    'all': [100, 150, 250, 500, 1000],
    'acp': [100, 150, 250, 500, 1000],
    'imp': [25, 50, 80, 100, 150],
}

MEDIUM_LC = {
    'all': [500, 1000, 1500, 2500],
    'acp': [500, 1000, 1500, 2500],
    'imp': [25, 50, 80, 100],
}

VARIANTS  = ['all', 'acp', 'imp']
NUM_RUNS  = 3
MAX_IDLE_HC = 2000

OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR   = OUTPUT_DIR / f'overnight_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

CHECKPOINT_FILE = RUN_DIR / 'checkpoint.txt'

# Run count
sprint_runs = (len(SPRINT_INSTANCES) * NUM_RUNS +
               sum(len(SPRINT_LC[v]) for v in VARIANTS) *
               len(SPRINT_INSTANCES) * NUM_RUNS)
medium_runs = (len(MEDIUM_INSTANCES) * NUM_RUNS +
               sum(len(MEDIUM_LC[v]) for v in VARIANTS) *
               len(MEDIUM_INSTANCES) * NUM_RUNS)
total_runs  = sprint_runs + medium_runs

print("=" * 80)
print("OVERNIGHT VALIDATION TEST - VARIANT-SPECIFIC Lc SWEEP")
print("=" * 80)
print()
print("SPRINT:")
print(f"  Instances: {len(SPRINT_INSTANCES)}")
for v in VARIANTS:
    print(f"  SCHC-{v} Lc: {SPRINT_LC[v]}")
print()
print("MEDIUM:")
print(f"  Instances: {[Path(p).stem for p in MEDIUM_INSTANCES]}")
for v in VARIANTS:
    print(f"  SCHC-{v} Lc: {MEDIUM_LC[v]}")
print()
print(f"Runs per config: {NUM_RUNS}")
print(f"Total runs: {total_runs}")
print(f"Output: {RUN_DIR}")
print("=" * 80)
print()


# ============================================================================
# HELPERS
# ============================================================================

def save_checkpoint(msg):
    with open(CHECKPOINT_FILE, 'a') as f:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{ts}] {msg}\n")
    print(f"  [CHECKPOINT] {msg}", flush=True)


def compute_stats(values):
    n   = len(values)
    avg = sum(values) / n
    std = (sum((x - avg) ** 2 for x in values) / n) ** 0.5
    return avg, std, min(values), max(values)


# ============================================================================
# RESULTS STORAGE
# ============================================================================

results_csv = RUN_DIR / 'results.csv'
csv_file    = open(results_csv, 'w', newline='')
writer      = csv.writer(csv_file)
writer.writerow([
    'scale', 'instance', 'algorithm', 'lc', 'run',
    'baseline', 'final', 'improvement', 'improvement_pct',
    'iterations', 'improving_moves', 'bound_updates', 'elapsed_time'
])

all_results   = defaultdict(list)  # keyed by (scale, variant, lc)
total_start   = time.time()
completed     = 0

save_checkpoint(f"Started - {total_runs} total runs")


# ============================================================================
# INSTANCE SWEEP FUNCTION
# ============================================================================

def sweep_instance(instance_path, scale, lc_map, label):
    global completed

    instance_name = Path(instance_path).stem
    instance      = load_instance(instance_path)
    baseline      = greedy_constructor(instance)
    baseline_pen  = evaluate_solution(baseline, instance)

    print()
    print(f"{'=' * 70}")
    print(f"  {label}: {instance_name}  (baseline: {baseline_pen})")
    print(f"{'=' * 70}")

    # HC baseline
    print(f"  HC baseline ({NUM_RUNS} runs):")
    hc_finals = []
    for run in range(1, NUM_RUNS + 1):
        completed += 1
        hc = HillClimbing(
            instance_data=instance,
            max_idle_iterations=MAX_IDLE_HC,
            random_seed=run
        )
        _, stats = hc.optimize(baseline, verbose=False)
        hc_finals.append(stats['final_penalty'])

        writer.writerow([
            scale, instance_name, 'HC', 0, run,
            baseline_pen, stats['final_penalty'],
            stats['improvement'], stats['improvement_percent'],
            stats['iterations'], 0, 0, stats['elapsed_time']
        ])
        all_results[(scale, 'HC', 0)].append(stats['final_penalty'])

        print(f"    Run {run}: {baseline_pen} -> {stats['final_penalty']} "
              f"({stats['improvement_percent']:.1f}%)  "
              f"Time: {stats['elapsed_time']:.1f}s", flush=True)

    hc_avg = sum(hc_finals) / len(hc_finals)
    csv_file.flush()
    print(f"  HC avg: {hc_avg:.1f}")
    print()

    # SCHC variants
    for variant in VARIANTS:
        lc_values = lc_map[variant]
        for lc in lc_values:
            print(f"  SCHC-{variant}  Lc={lc}  "
                  f"(stagnation limit: {max(30000, lc*500):,}"
                  if variant == 'imp'
                  else f"  SCHC-{variant}  Lc={lc}",
                  flush=True)

            run_finals = []
            for run in range(1, NUM_RUNS + 1):
                completed += 1
                elapsed   = time.time() - total_start
                remaining = total_runs - completed
                eta_h     = (elapsed / completed * remaining) / 3600

                print(f"    Run {run}/{NUM_RUNS} "
                      f"[{completed}/{total_runs}, ETA {eta_h:.1f}h]...",
                      end=" ", flush=True)

                schc = SCHC(
                    instance_data=instance,
                    Lc=lc,
                    variant=variant,
                    random_seed=run,
                    print_interval=999999999  # suppress per-iter output
                )
                _, stats = schc.optimize(baseline, verbose=False)
                run_finals.append(stats['final_penalty'])

                writer.writerow([
                    scale, instance_name, f'SCHC-{variant}', lc, run,
                    baseline_pen, stats['final_penalty'],
                    stats['improvement'], stats['improvement_percent'],
                    stats['iterations'],
                    stats.get('improving_moves', 0),
                    stats['bound_updates'],
                    stats['elapsed_time']
                ])
                all_results[(scale, variant, lc)].append(stats['final_penalty'])

                imp_info = (f"  ImpMoves: {stats.get('improving_moves', 0):,}"
                            if variant == 'imp' else "")
                print(f"{baseline_pen} -> {stats['final_penalty']} "
                      f"({stats['improvement_percent']:.1f}%)  "
                      f"Updates: {stats['bound_updates']}  "
                      f"Iters: {stats['iterations']:,}  "
                      f"Time: {stats['elapsed_time']:.1f}s"
                      f"{imp_info}", flush=True)

            avg_f = sum(run_finals) / len(run_finals)
            vs_hc = avg_f - hc_avg
            print(f"  -> avg: {avg_f:.1f}  vs HC: {vs_hc:+.1f}")
            print(flush=True)
            csv_file.flush()

    save_checkpoint(f"Completed {instance_name} [{completed}/{total_runs}]")


# ============================================================================
# PHASE 1: SPRINT
# ============================================================================

print()
print("=" * 80)
print("PHASE 1: SPRINT INSTANCES")
print("=" * 80)

for path in SPRINT_INSTANCES:
    sweep_instance(path, 'sprint', SPRINT_LC, 'Sprint')

phase1_elapsed = time.time() - total_start
save_checkpoint(f"Phase 1 (sprint) done - {phase1_elapsed/3600:.2f}h")


# ============================================================================
# PHASE 2: MEDIUM
# ============================================================================

print()
print("=" * 80)
print("PHASE 2: MEDIUM INSTANCES")
print("=" * 80)

for path in MEDIUM_INSTANCES:
    sweep_instance(path, 'medium', MEDIUM_LC, 'Medium')

phase2_elapsed = time.time() - total_start - phase1_elapsed
save_checkpoint(f"Phase 2 (medium) done - {phase2_elapsed/3600:.2f}h")


# ============================================================================
# ANALYSIS
# ============================================================================

csv_file.close()
total_elapsed = time.time() - total_start

def print_and_save_summary(scale, lc_map, instances, filename):
    lines = []
    lines.append("=" * 80)
    lines.append(f"SUMMARY: {scale.upper()} INSTANCES")
    lines.append("=" * 80)

    hc_results = all_results.get((scale, 'HC', 0), [])
    hc_avg     = sum(hc_results) / len(hc_results) if hc_results else 0
    lines.append(f"\nHC baseline avg: {hc_avg:.1f}")
    lines.append("")

    for variant in VARIANTS:
        lines.append(f"SCHC-{variant}:")
        lines.append(f"  {'Lc':<6}  {'AvgFinal':>10}  {'StdDev':>8}  "
                     f"{'Best':>6}  {'Worst':>6}  {'vs HC':>8}")
        lines.append("  " + "-" * 55)

        best_lc  = None
        best_avg = float('inf')

        for lc in lc_map[variant]:
            results = all_results.get((scale, variant, lc), [])
            if not results:
                continue
            avg, std, best, worst = compute_stats(results)
            vs_hc = avg - hc_avg
            marker = ""
            if avg < best_avg:
                best_avg = avg
                best_lc  = lc
            lines.append(f"  {lc:<6}  {avg:>10.1f}  {std:>8.1f}  "
                         f"{best:>6}  {worst:>6}  {vs_hc:>+8.1f}")

        lines.append(f"  Optimal Lc: {best_lc}  (avg: {best_avg:.1f})")
        lines.append("")

    summary_text = "\n".join(lines)
    print(summary_text)

    with open(RUN_DIR / filename, 'w') as f:
        f.write(summary_text)


print()
print_and_save_summary('sprint', SPRINT_LC, SPRINT_INSTANCES, 'sprint_summary.txt')
print_and_save_summary('medium', MEDIUM_LC, MEDIUM_INSTANCES, 'medium_summary.txt')

print()
print("=" * 80)
print("OVERNIGHT TEST COMPLETE")
print("=" * 80)
print(f"Total runtime:   {total_elapsed / 3600:.2f} hours")
print(f"Phase 1 sprint:  {phase1_elapsed / 3600:.2f} hours")
print(f"Phase 2 medium:  {phase2_elapsed / 3600:.2f} hours")
print(f"Runs completed:  {completed}")
print(f"Avg per run:     {total_elapsed / completed:.1f}s")
print(f"Results:         {results_csv}")
print(f"Checkpoint:      {CHECKPOINT_FILE}")
print("=" * 80)