'''
Single Instance Sweep Runner - All Variants
============================================
Runs the HC baseline plus all three SCHC variants for a single INRC-I
instance. This is the script that produced every result in
results/raw/, called once per instance by the Slurm job arrays in
experiments/slurm/.

Usage (from the repository root):
    python experiments/run_instance_sweep.py <scale> <index>

    scale : "sprint", "medium", or "long"
    index : integer 1 through 10 (sprint) or 1 through 5 (medium/long)

Lc ranges (empirically calibrated):
    SCHC-all / SCHC-acp:
        Sprint : [100, 250, 500, 1000, 1500]
        Medium : [500, 1000, 1500, 2500]
        Long   : [500, 1000, 1500, 2500]

    SCHC-imp (scaled by improving move rate):
        Sprint : [25, 50, 80, 100]
        Medium : [15, 25, 40, 50]
        Long   : [15, 25, 40, 50]

Termination:
    HC:                  no improvement for 2000 consecutive iterations
    SCHC-all / SCHC-acp: adaptive per Bykov & Petrovic (2016)
    SCHC-imp:            stagnation-based (no new best for max(30000, Lc*500) iters)

Each run uses its run number (1-10) as the random seed, so every result
in results/raw/ can be regenerated exactly.

Approximate single-core wall times on Falcon (htc_genoa):
    sprint instance ~2.5 h, medium instance ~20 h, long instance ~50-58 h
'''

import sys
from pathlib import Path
import time
import csv
from datetime import datetime
from collections import defaultdict

if len(sys.argv) != 3:
    print("Usage: python experiments/run_instance_sweep.py <scale> <index>")
    print("  scale : 'sprint', 'medium', or 'long'")
    print("  index : 1 through 10 (sprint) or 1 through 5 (medium/long)")
    sys.exit(1)

SCALE = sys.argv[1].lower()
if SCALE not in ('sprint', 'medium', 'long'):
    print(f"ERROR: scale must be 'sprint', 'medium' or 'long'")
    sys.exit(1)

try:
    INDEX = int(sys.argv[2])
except ValueError:
    print(f"ERROR: index must be an integer")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.hill_climbing import HillClimbing
from algorithms.schc import SCHC
from constraints import evaluate_solution

INSTANCE_PATH = REPO_ROOT / 'data' / 'inrc1' / f'INRC1_{SCALE}{INDEX:02d}.json'
INSTANCE_NAME = f'INRC1_{SCALE}{INDEX:02d}'

VARIANTS_CONFIG = {
    'all': {
        'sprint': [100, 250, 500, 1000, 1500],
        'medium': [500, 1000, 1500, 2500],
        'long':   [500, 1000, 1500, 2500],
    },
    'acp': {
        'sprint': [100, 250, 500, 1000, 1500],
        'medium': [500, 1000, 1500, 2500],
        'long':   [500, 1000, 1500, 2500],
    },
    'imp': {
        'sprint': [25, 50, 80, 100],
        'medium': [15, 25, 40, 50],
        'long':   [15, 25, 40, 50],
    },
}

VARIANTS    = ['all', 'acp', 'imp']
NUM_RUNS    = 10
MAX_IDLE_HC = 2000

OUTPUT_DIR = REPO_ROOT / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR   = OUTPUT_DIR / f'{SCALE}_{INDEX:02d}_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

CHECKPOINT_FILE = RUN_DIR / 'checkpoint.txt'

TOTAL_RUNS = NUM_RUNS + sum(
    len(VARIANTS_CONFIG[v][SCALE]) * NUM_RUNS for v in VARIANTS
)

print("=" * 70)
print(f"INSTANCE SWEEP: {INSTANCE_NAME}  (all variants)")
print("=" * 70)
for v in VARIANTS:
    print(f"  SCHC-{v} Lc: {VARIANTS_CONFIG[v][SCALE]}")
print(f"  Runs per config: {NUM_RUNS}  |  Total: {TOTAL_RUNS}")
print(f"  Output: {RUN_DIR}")
print("=" * 70)
print()


def save_checkpoint(message):
    with open(CHECKPOINT_FILE, 'a') as f:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{ts}] {message}\n")
    print(f"  [CHECKPOINT] {message}", flush=True)


def compute_stats(values):
    n   = len(values)
    avg = sum(values) / n
    std = (sum((x - avg) ** 2 for x in values) / n) ** 0.5
    return avg, std, min(values), max(values)


if not INSTANCE_PATH.exists():
    print(f"ERROR: Instance file not found: {INSTANCE_PATH}")
    sys.exit(1)

instance     = load_instance(str(INSTANCE_PATH))
baseline     = greedy_constructor(instance)
baseline_pen = evaluate_solution(baseline, instance)

print(f"Baseline: {baseline_pen}")
print()

results_csv = RUN_DIR / 'results.csv'
csv_file    = open(results_csv, 'w', newline='')
csv_writer  = csv.writer(csv_file)
csv_writer.writerow([
    'instance', 'scale', 'algorithm', 'lc', 'run',
    'baseline_penalty', 'final_penalty',
    'improvement', 'improvement_pct',
    'iterations', 'improving_moves', 'bound_updates', 'elapsed_time'
])

results_store = defaultdict(list)
hc_finals     = []
total_start   = time.time()
completed     = 0

save_checkpoint(f"Started {INSTANCE_NAME}")

# HC baseline
print(f"HC baseline ({NUM_RUNS} runs):")
for run in range(1, NUM_RUNS + 1):
    completed += 1
    eta_h = (((time.time() - total_start) / completed)
             * (TOTAL_RUNS - completed)) / 3600
    print(f"  Run {run}/{NUM_RUNS} [{completed}/{TOTAL_RUNS}] "
          f"(ETA: {eta_h:.1f}h)...", end=" ", flush=True)

    hc = HillClimbing(instance_data=instance,
                      max_idle_iterations=MAX_IDLE_HC,
                      random_seed=run)
    _, stats = hc.optimize(baseline, verbose=False)
    hc_finals.append(stats['final_penalty'])

    csv_writer.writerow([
        INSTANCE_NAME, SCALE, 'HC', 'N/A', run,
        baseline_pen, stats['final_penalty'],
        stats['improvement'], stats['improvement_percent'],
        stats['iterations'], 0, 0, stats['elapsed_time']
    ])
    print(f"{baseline_pen} -> {stats['final_penalty']} "
          f"({stats['improvement_percent']:.1f}%)  "
          f"Time: {stats['elapsed_time']:.1f}s")

hc_avg = sum(hc_finals) / len(hc_finals)
save_checkpoint(f"HC complete  avg={hc_avg:.1f}")
csv_file.flush()
print()

# SCHC variants
for variant in VARIANTS:
    lc_values = VARIANTS_CONFIG[variant][SCALE]
    for lc in lc_values:
        print(f"SCHC-{variant}  Lc={lc}:")
        for run in range(1, NUM_RUNS + 1):
            completed += 1
            eta_h = (((time.time() - total_start) / completed)
                     * (TOTAL_RUNS - completed)) / 3600
            print(f"  Run {run}/{NUM_RUNS} [{completed}/{TOTAL_RUNS}] "
                  f"(ETA: {eta_h:.1f}h)...", end=" ", flush=True)

            schc = SCHC(
                instance_data=instance,
                Lc=lc,
                variant=variant,
                random_seed=run,
                print_interval=999999999
            )
            _, stats = schc.optimize(baseline, verbose=False)

            csv_writer.writerow([
                INSTANCE_NAME, SCALE, f'SCHC-{variant}', lc, run,
                baseline_pen, stats['final_penalty'],
                stats['improvement'], stats['improvement_percent'],
                stats['iterations'],
                stats.get('improving_moves', 0),
                stats['bound_updates'],
                stats['elapsed_time']
            ])

            results_store[(variant, lc)].append({
                'final': stats['final_penalty'],
                'time':  stats['elapsed_time'],
                'bound_updates': stats['bound_updates'],
                'improving_moves': stats.get('improving_moves', 0),
                'iterations': stats['iterations'],
            })

            imp_info = (f"  ImpMoves: {stats.get('improving_moves',0):,}"
                        if variant == 'imp' else "")
            print(f"{baseline_pen} -> {stats['final_penalty']} "
                  f"({stats['improvement_percent']:.1f}%)  "
                  f"Updates: {stats['bound_updates']}  "
                  f"Iters: {stats['iterations']:,}  "
                  f"Time: {stats['elapsed_time']:.1f}s{imp_info}")

        save_checkpoint(f"SCHC-{variant} Lc={lc} complete")
        csv_file.flush()
        print()

csv_file.close()
total_elapsed = time.time() - total_start

# Summary
print("=" * 70)
print(f"SUMMARY: {INSTANCE_NAME}")
print("=" * 70)
print(f"\nHC avg: {hc_avg:.1f}\n")

for variant in VARIANTS:
    lc_values = VARIANTS_CONFIG[variant][SCALE]
    print(f"SCHC-{variant}:")
    print(f"  {'Lc':<6}  {'AvgPenalty':>11}  {'StdDev':>8}  "
          f"{'Best':>6}  {'Worst':>6}  {'vs HC':>8}  {'AvgTime':>9}")
    print("  " + "-" * 65)

    best_lc  = None
    best_avg = float('inf')

    for lc in lc_values:
        results = results_store[(variant, lc)]
        if not results:
            continue
        finals = [r['final'] for r in results]
        times  = [r['time'] for r in results]
        avg, std, best, worst = compute_stats(finals)
        avg_t = sum(times) / len(times)
        vs_hc = avg - hc_avg
        if avg < best_avg:
            best_avg = avg
            best_lc  = lc
        marker = "  <-- best" if lc == best_lc else ""
        print(f"  {lc:<6}  {avg:>11.1f}  {std:>8.1f}  "
              f"{best:>6}  {worst:>6}  {vs_hc:>+8.1f}  "
              f"{avg_t:>8.1f}s{marker}")

    print(f"  Optimal Lc: {best_lc}  (avg: {best_avg:.1f})\n")

print("=" * 70)
print(f"Total time: {total_elapsed/3600:.2f}h")
print(f"Results:    {results_csv}")
print("=" * 70)

save_checkpoint(f"Complete {total_elapsed/3600:.2f}h")
