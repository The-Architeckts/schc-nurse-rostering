'''
Single Instance Sweep Runner
=============================
Runs a complete Lc sweep for a single INRC-I instance. Designed to be
called by Slurm job arrays, receiving the instance index (1-5) as a
command-line argument. Can also be run directly for testing.

Usage:
    python run_instance_sweep.py <scale> <index>

    scale : "medium" or "long"
    index : integer 1 through 5

Examples:
    python run_instance_sweep.py medium 1
    python run_instance_sweep.py long 3

Lc ranges:
    Medium : [500, 1000, 1500, 2500, 5000, 7500]
    Long   : [500, 1000, 1500, 2500, 5000, 7500, 10000]

Termination:
    MAX_IDLE_SCHC scales as max(10000, Lc * 10) to prevent premature
    termination at large counter values. See methodology notes below.

Output:
    outputs/<scale>_instance<index>_<timestamp>/
        results.csv
        checkpoint.txt
        lc_comparison_<variant>.png  (if matplotlib available)
'''

import sys
from pathlib import Path
import time
import csv
from datetime import datetime
from collections import defaultdict

# ---------------------------------------------------------------------------
# ARGUMENT PARSING
# ---------------------------------------------------------------------------

if len(sys.argv) != 3:
    print("Usage: python run_instance_sweep.py <scale> <index>")
    print("  scale : 'medium' or 'long'")
    print("  index : 1 through 5")
    sys.exit(1)

SCALE = sys.argv[1].lower()
if SCALE not in ('medium', 'long'):
    print(f"ERROR: scale must be 'medium' or 'long', got '{SCALE}'")
    sys.exit(1)

try:
    INDEX = int(sys.argv[2])
    if not 1 <= INDEX <= 5:
        raise ValueError
except ValueError:
    print(f"ERROR: index must be an integer between 1 and 5, got '{sys.argv[2]}'")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))

from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.hill_climbing import HillClimbing
from algorithms.schc import SCHC
from constraints import evaluate_solution

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

INSTANCE_PATH = f'data/inrc1/INRC1_{SCALE}{INDEX:02d}.json'
INSTANCE_NAME = f'INRC1_{SCALE}{INDEX:02d}'

VARIANTS = ['all', 'acp', 'imp']

if SCALE == 'medium':
    LC_VALUES = [500, 1000, 1500, 2500, 5000, 7500]
else:
    LC_VALUES = [500, 1000, 1500, 2500, 5000, 7500, 10000]

NUM_RUNS = 10

MAX_IDLE_HC = 2000

def get_max_idle_schc(lc):
    '''
    Scale idle termination limit with Lc to ensure the algorithm receives
    a fair number of bound epochs regardless of counter size. Without
    scaling, large Lc values terminate after barely one epoch with no
    acceptance, producing misleadingly poor results. The formula guarantees
    at least 10 full epochs of idle tolerance, with a hard floor of 10000.
    '''
    return max(10000, lc * 10)

OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR = OUTPUT_DIR / f'{SCALE}_{INDEX:02d}_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

CHECKPOINT_FILE = RUN_DIR / 'checkpoint.txt'

SCHC_RUNS  = len(VARIANTS) * len(LC_VALUES) * NUM_RUNS
HC_RUNS    = NUM_RUNS
TOTAL_RUNS = SCHC_RUNS + HC_RUNS

print("=" * 70)
print(f"SINGLE INSTANCE SWEEP: {INSTANCE_NAME}")
print("=" * 70)
print(f"Scale:              {SCALE}")
print(f"Instance index:     {INDEX}")
print(f"Instance file:      {INSTANCE_PATH}")
print(f"SCHC variants:      {VARIANTS}")
print(f"Lc values:          {LC_VALUES}")
print(f"Runs per config:    {NUM_RUNS}")
print()
print(f"SCHC runs: {len(VARIANTS)} variants x {len(LC_VALUES)} Lc x {NUM_RUNS} runs = {SCHC_RUNS}")
print(f"HC runs:   {NUM_RUNS}")
print(f"Total:     {TOTAL_RUNS}")
print()
print(f"MAX_IDLE_SCHC by Lc:")
for lc in LC_VALUES:
    print(f"  Lc={lc:<6}  MAX_IDLE={get_max_idle_schc(lc)}")
print()
print(f"Output directory: {RUN_DIR}")
print("=" * 70)
print()


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def save_checkpoint(message):
    with open(CHECKPOINT_FILE, 'a') as f:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{ts}] {message}\n")
    print(f"  [CHECKPOINT] {message}")


def compute_stats(values):
    n   = len(values)
    avg = sum(values) / n
    std = (sum((x - avg) ** 2 for x in values) / n) ** 0.5
    return avg, std, min(values), max(values)


def save_lc_plot(variant, lc_values, results_by_lc):
    if not HAS_MATPLOTLIB:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    lc_avgs, lc_stds = [], []

    for lc in lc_values:
        results = results_by_lc[lc]
        if not results:
            lc_avgs.append(0)
            lc_stds.append(0)
            continue
        finals = [r['final'] for r in results]
        avg, std, _, _ = compute_stats(finals)
        lc_avgs.append(avg)
        lc_stds.append(std)

    x = range(len(lc_values))
    ax.bar(x, lc_avgs, alpha=0.75, yerr=lc_stds, capsize=5)
    ax.set_title(f'{INSTANCE_NAME} - SCHC-{variant} Lc Sensitivity',
                 fontsize=12, fontweight='bold')
    ax.set_xlabel('Lc Value')
    ax.set_ylabel('Avg Final Penalty (10 runs)')
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(lc) for lc in lc_values])
    ax.grid(True, alpha=0.3, axis='y')

    for i, (v, s) in enumerate(zip(lc_avgs, lc_stds)):
        if v > 0:
            ax.text(i, v + s + max(lc_avgs) * 0.01, f'{v:.1f}',
                    ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(RUN_DIR / f'lc_sensitivity_{variant}.png', dpi=150, bbox_inches='tight')
    plt.close()


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------

if not Path(INSTANCE_PATH).exists():
    print(f"ERROR: Instance file not found: {INSTANCE_PATH}")
    print("Check that the data/inrc1/ directory is present and populated.")
    sys.exit(1)

instance     = load_instance(INSTANCE_PATH)
baseline     = greedy_constructor(instance)
baseline_pen = evaluate_solution(baseline, instance)

print(f"Baseline (greedy) penalty: {baseline_pen}")
print()

results_csv_path = RUN_DIR / 'results.csv'
csv_file         = open(results_csv_path, 'w', newline='')
csv_writer       = csv.writer(csv_file)
csv_writer.writerow([
    'instance', 'scale', 'algorithm', 'lc', 'run',
    'baseline_penalty', 'final_penalty',
    'improvement', 'improvement_pct',
    'iterations', 'bound_updates', 'elapsed_time'
])

all_results      = []
by_lc_variant    = defaultdict(list)
results_by_var   = {v: defaultdict(list) for v in VARIANTS}
total_start      = time.time()
completed        = 0

save_checkpoint(f"Started {INSTANCE_NAME}")

# ------------------------------------------------------------------
# HC BASELINE
# ------------------------------------------------------------------
print(f"Running HC baseline ({NUM_RUNS} runs):")

for run in range(1, NUM_RUNS + 1):
    completed += 1
    elapsed = time.time() - total_start
    eta_h   = ((elapsed / completed) * (TOTAL_RUNS - completed)) / 3600

    print(f"  Run {run}/{NUM_RUNS} [{completed}/{TOTAL_RUNS}] "
          f"(ETA: {eta_h:.1f}h)...", end=" ", flush=True)

    hc = HillClimbing(
        instance_data=instance,
        max_idle_iterations=MAX_IDLE_HC,
        random_seed=run
    )
    _, stats = hc.optimize(baseline, verbose=False)

    csv_writer.writerow([
        INSTANCE_NAME, SCALE, 'HC', 'N/A', run,
        baseline_pen, stats['final_penalty'],
        stats['improvement'], stats['improvement_percent'],
        stats['iterations'], 0, stats['elapsed_time']
    ])

    result = {
        'algorithm': 'HC', 'lc': None, 'run': run,
        'baseline': baseline_pen,
        'final': stats['final_penalty'],
        'improvement_pct': stats['improvement_percent'],
        'iterations': stats['iterations'],
        'bound_updates': 0,
        'time': stats['elapsed_time']
    }
    all_results.append(result)
    by_lc_variant['HC'].append(result)

    print(f"{baseline_pen} -> {stats['final_penalty']} "
          f"({stats['improvement_percent']:.1f}%), "
          f"Time: {stats['elapsed_time']:.1f}s")

save_checkpoint("HC baseline complete")
print()

# ------------------------------------------------------------------
# SCHC VARIANTS x LC VALUES
# ------------------------------------------------------------------
for variant in VARIANTS:
    for lc in LC_VALUES:
        idle_limit = get_max_idle_schc(lc)
        print(f"Testing SCHC-{variant} (Lc={lc}, MAX_IDLE={idle_limit}):")

        for run in range(1, NUM_RUNS + 1):
            completed += 1
            elapsed = time.time() - total_start
            eta_h   = ((elapsed / completed) * (TOTAL_RUNS - completed)) / 3600

            print(f"  Run {run}/{NUM_RUNS} [{completed}/{TOTAL_RUNS}] "
                  f"(ETA: {eta_h:.1f}h)...", end=" ", flush=True)

            schc = SCHC(
                instance_data=instance,
                Lc=lc,
                variant=variant,
                max_idle_iterations=idle_limit,
                random_seed=run
            )
            _, stats = schc.optimize(baseline, verbose=False)

            csv_writer.writerow([
                INSTANCE_NAME, SCALE, f'SCHC-{variant}', lc, run,
                baseline_pen, stats['final_penalty'],
                stats['improvement'], stats['improvement_percent'],
                stats['iterations'], stats['bound_updates'],
                stats['elapsed_time']
            ])

            result = {
                'algorithm': f'SCHC-{variant}',
                'lc': lc, 'run': run,
                'baseline': baseline_pen,
                'final': stats['final_penalty'],
                'improvement_pct': stats['improvement_percent'],
                'iterations': stats['iterations'],
                'bound_updates': stats['bound_updates'],
                'time': stats['elapsed_time']
            }
            all_results.append(result)
            by_lc_variant[f'SCHC-{variant}-{lc}'].append(result)
            results_by_var[variant][lc].append(result)

            print(f"{baseline_pen} -> {stats['final_penalty']} "
                  f"({stats['improvement_percent']:.1f}%), "
                  f"Updates: {stats['bound_updates']}, "
                  f"Time: {stats['elapsed_time']:.1f}s")

        print()

    save_checkpoint(f"SCHC-{variant} complete")
    save_lc_plot(variant, LC_VALUES, results_by_var[variant])
    csv_file.flush()

csv_file.close()
total_elapsed = time.time() - total_start


# ---------------------------------------------------------------------------
# ANALYSIS SUMMARY
# ---------------------------------------------------------------------------

print("=" * 70)
print(f"RESULTS SUMMARY: {INSTANCE_NAME}")
print("=" * 70)
print()

hc_results = by_lc_variant.get('HC', [])
hc_avg     = sum(r['final'] for r in hc_results) / len(hc_results) if hc_results else 0
hc_times   = [r['time'] for r in hc_results]
hc_avg_t   = sum(hc_times) / len(hc_times) if hc_times else 0
print(f"HC baseline:  avg penalty = {hc_avg:.1f}  avg time = {hc_avg_t:.1f}s")
print()

for variant in VARIANTS:
    print(f"SCHC-{variant}:")
    print(f"  {'Lc':<6}  {'AvgPenalty':>11}  {'StdDev':>8}  "
          f"{'Best':>6}  {'Worst':>6}  {'vs HC':>8}  {'AvgTime':>9}")
    print("  " + "-" * 65)

    best_lc  = None
    best_avg = float('inf')

    for lc in LC_VALUES:
        key = f'SCHC-{variant}-{lc}'
        if key not in by_lc_variant:
            continue
        results  = by_lc_variant[key]
        finals   = [r['final'] for r in results]
        times    = [r['time'] for r in results]
        avg, std, best, worst = compute_stats(finals)
        avg_t    = sum(times) / len(times)
        vs_hc    = avg - hc_avg
        marker   = '  <-- best' if avg < best_avg else ''

        print(f"  {lc:<6}  {avg:>11.1f}  {std:>8.1f}  "
              f"{best:>6}  {worst:>6}  {vs_hc:>+8.1f}  {avg_t:>8.1f}s{marker}")

        if avg < best_avg:
            best_avg = avg
            best_lc  = lc

    print(f"  Optimal Lc: {best_lc}  (avg {best_avg:.1f})")
    print()

print("=" * 70)
print(f"RUNTIME SUMMARY")
print("=" * 70)
print(f"Total elapsed:      {total_elapsed / 3600:.2f} hours ({total_elapsed / 60:.1f} min)")
print(f"Total runs:         {completed}")
print(f"Avg time per run:   {total_elapsed / completed:.1f}s")
print()
print(f"Results saved to:   {RUN_DIR}")
print(f"CSV:                {results_csv_path}")
print(f"Checkpoint log:     {CHECKPOINT_FILE}")
print("=" * 70)

save_checkpoint(f"Complete - {total_elapsed / 3600:.2f}h total")