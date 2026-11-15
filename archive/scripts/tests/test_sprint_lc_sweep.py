'''
Sprint Lc Validation Sweep - Post Bug Fix
==========================================
Validates optimal Lc values for all three SCHC variants after
fixing the acp and imp implementation bugs.

Tests all 10 sprint instances across Lc values [100, 150, 250, 500, 1000]
with 10 runs per configuration to establish statistically reliable optima.

CONTEXT:
- SCHC-all: was correct throughout, confirming previous Lc findings
- SCHC-acp: was Lc-insensitive due to per-acceptance bound update bug
- SCHC-imp: improvement trigger was never firing due to premature best update

This sweep re-establishes optimal Lc for corrected acp and imp variants,
and confirms all variant findings before committing to the full final test.

EXPECTED RUNTIME: ~3-5 hours
RUNS:
  10 instances x 3 variants x 5 Lc values x 10 runs = 1500 SCHC runs
  10 instances x 10 HC runs                          =  100 HC runs
  Total: 1600 runs
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

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ============================================================================
# CONFIGURATION
# ============================================================================

INSTANCES = [
    f'data/inrc1/INRC1_sprint{i:02d}.json' for i in range(1, 11)
]

VARIANTS = ['all', 'acp', 'imp']

LC_VALUES = [100, 150, 250, 500, 1000]

NUM_RUNS = 10

MAX_IDLE_HC   = 2000
MAX_IDLE_SCHC = 10000

OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR = OUTPUT_DIR / f'sprint_lc_sweep_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

CHECKPOINT_FILE = RUN_DIR / 'checkpoint.txt'

SCHC_RUNS = len(INSTANCES) * len(VARIANTS) * len(LC_VALUES) * NUM_RUNS
HC_RUNS   = len(INSTANCES) * NUM_RUNS
TOTAL_RUNS = SCHC_RUNS + HC_RUNS

print("=" * 80)
print("SPRINT INSTANCES - Lc VALIDATION SWEEP (POST BUG FIX)")
print("=" * 80)
print(f"Testing {len(INSTANCES)} sprint instances")
print(f"SCHC variants: {VARIANTS}")
print(f"Lc values: {LC_VALUES}")
print(f"Runs per configuration: {NUM_RUNS}")
print()
print(f"SCHC runs: {len(INSTANCES)} x {len(VARIANTS)} x {len(LC_VALUES)} x {NUM_RUNS} = {SCHC_RUNS}")
print(f"HC runs:   {len(INSTANCES)} x {NUM_RUNS} = {HC_RUNS}")
print(f"Total runs: {TOTAL_RUNS}")
print()
print(f"Output directory: {RUN_DIR}")
print("=" * 80)
print()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_checkpoint(message):
    with open(CHECKPOINT_FILE, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")


def compute_stats(values):
    n = len(values)
    avg = sum(values) / n
    std = (sum((x - avg) ** 2 for x in values) / n) ** 0.5
    return avg, std, min(values), max(values)


def save_lc_comparison_plot(instance_name, results_by_variant_lc):
    if not HAS_MATPLOTLIB:
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(f'{instance_name} - Lc Sensitivity by Variant (Post Fix)',
                 fontsize=14, fontweight='bold')

    colors = {100: 'blue', 150: 'green', 250: 'orange', 500: 'red', 1000: 'purple'}

    for idx, variant in enumerate(VARIANTS):
        ax = axes[idx]
        lc_avgs = []
        lc_stds = []

        for lc in LC_VALUES:
            results = results_by_variant_lc[variant][lc]
            if not results:
                continue
            finals = [r['final'] for r in results]
            avg, std, _, _ = compute_stats(finals)
            lc_avgs.append(avg)
            lc_stds.append(std)

        x = range(len(LC_VALUES))
        ax.bar(x, lc_avgs, color=[colors[lc] for lc in LC_VALUES],
               alpha=0.7, yerr=lc_stds, capsize=5)
        ax.set_title(f'SCHC-{variant}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Lc Value')
        ax.set_ylabel('Avg Final Penalty')
        ax.set_xticks(x)
        ax.set_xticklabels(LC_VALUES)
        ax.grid(True, alpha=0.3, axis='y')

        for i, (v, s) in enumerate(zip(lc_avgs, lc_stds)):
            ax.text(i, v + s + max(lc_avgs) * 0.01, f'{v:.1f}',
                    ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    filename = f'{instance_name}_lc_comparison.png'
    plt.savefig(RUN_DIR / filename, dpi=150, bbox_inches='tight')
    plt.close()


def save_aggregate_plot(by_lc_variant):
    if not HAS_MATPLOTLIB:
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Sprint Lc Sensitivity - Aggregate (Post Bug Fix)',
                 fontsize=16, fontweight='bold')

    colors = {100: 'blue', 150: 'green', 250: 'orange', 500: 'red', 1000: 'purple'}

    for idx, variant in enumerate(VARIANTS):
        ax = axes[idx]
        lc_avgs, lc_stds = [], []

        for lc in LC_VALUES:
            key = f'SCHC-{variant}-{lc}'
            if key not in by_lc_variant:
                continue
            finals = [r['final'] for r in by_lc_variant[key]]
            avg, std, _, _ = compute_stats(finals)
            lc_avgs.append(avg)
            lc_stds.append(std)

        x = range(len(LC_VALUES))
        ax.bar(x, lc_avgs, color=[colors[lc] for lc in LC_VALUES],
               alpha=0.7, yerr=lc_stds, capsize=5)
        ax.set_title(f'SCHC-{variant}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Lc Value')
        ax.set_ylabel('Avg Final Penalty')
        ax.set_xticks(x)
        ax.set_xticklabels(LC_VALUES)
        ax.grid(True, alpha=0.3, axis='y')

        for i, (v, s) in enumerate(zip(lc_avgs, lc_stds)):
            ax.text(i, v + s + max(lc_avgs) * 0.01, f'{v:.1f}',
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(RUN_DIR / 'aggregate_lc_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Aggregate plot saved.")


def save_scaling_context_plot(variant_optima, hc_avg):
    '''
    Plots optimal Lc per variant alongside HC baseline for context.
    '''
    if not HAS_MATPLOTLIB:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(VARIANTS))
    opt_avgs = [variant_optima[v]['avg'] for v in VARIANTS]
    opt_lcs  = [variant_optima[v]['lc'] for v in VARIANTS]
    colors   = ['steelblue', 'darkorange', 'forestgreen']

    bars = ax.bar(x, opt_avgs, color=colors, alpha=0.8, width=0.5)
    ax.axhline(y=hc_avg, color='red', linestyle='--', linewidth=2,
               label=f'HC Baseline ({hc_avg:.1f})')

    ax.set_title('Sprint: SCHC Variants at Optimal Lc vs HC Baseline (Post Fix)',
                 fontsize=13, fontweight='bold')
    ax.set_ylabel('Avg Final Penalty (lower is better)')
    ax.set_xticks(x)
    ax.set_xticklabels([f'SCHC-{v}\n(Lc={opt_lcs[v_idx]})'
                        for v_idx, v in enumerate(VARIANTS)])
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')

    for i, v in enumerate(opt_avgs):
        ax.text(i, v + max(opt_avgs) * 0.01, f'{v:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(RUN_DIR / 'variant_comparison_at_optimal_lc.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Variant comparison plot saved.")


# ============================================================================
# MAIN TESTING LOOP
# ============================================================================

all_results  = []
by_lc_variant = defaultdict(list)

summary_csv_path = RUN_DIR / 'summary.csv'
csv_file   = open(summary_csv_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'Instance', 'Algorithm', 'Lc', 'Run',
    'Baseline', 'Final', 'Improvement', 'Improvement_Pct',
    'Iterations', 'Bound_Updates', 'Time'
])

total_start  = time.time()
completed    = 0

save_checkpoint(f"Starting - {TOTAL_RUNS} total runs")

for instance_path in INSTANCES:
    if not Path(instance_path).exists():
        print(f"WARNING: Skipping {instance_path} - file not found")
        save_checkpoint(f"Skipped {instance_path}")
        continue

    instance_name = Path(instance_path).stem

    print("=" * 80)
    print(f"TESTING: {instance_name}")
    print("=" * 80)
    save_checkpoint(f"Started {instance_name}")

    instance = load_instance(instance_path)
    n_nurses = len(instance['nurses'])
    n_days   = instance['period']
    print(f"Loaded: {instance['name']} ({n_nurses} nurses, {n_days} days)")

    baseline         = greedy_constructor(instance)
    baseline_penalty = evaluate_solution(baseline, instance)
    print(f"Baseline penalty: {baseline_penalty}")
    print()

    results_by_variant_lc = defaultdict(lambda: defaultdict(list))

    # ------------------------------------------------------------------
    # HC BASELINE
    # ------------------------------------------------------------------
    print("  Testing HC (baseline):")
    for run in range(1, NUM_RUNS + 1):
        completed += 1
        elapsed   = time.time() - total_start
        eta_h     = (elapsed / completed) * (TOTAL_RUNS - completed) / 3600

        print(f"    Run {run}/{NUM_RUNS} [{completed}/{TOTAL_RUNS}] "
              f"(ETA: {eta_h:.1f}h)...", end=" ", flush=True)

        hc = HillClimbing(
            instance_data=instance,
            max_idle_iterations=MAX_IDLE_HC,
            random_seed=run
        )
        _, stats = hc.optimize(baseline, verbose=False)

        csv_writer.writerow([
            instance_name, 'HC', 0, run,
            baseline_penalty, stats['final_penalty'],
            stats['improvement'], stats['improvement_percent'],
            stats['iterations'], 0, stats['elapsed_time']
        ])

        result = {
            'instance': instance_name, 'algorithm': 'HC',
            'lc': 0, 'run': run,
            'baseline': baseline_penalty, 'final': stats['final_penalty'],
            'improvement_pct': stats['improvement_percent'],
            'bound_updates': 0, 'time': stats['elapsed_time'],
            'penalty_history': stats['penalty_history']
        }
        all_results.append(result)
        by_lc_variant['HC'].append(result)

        print(f"{baseline_penalty} → {stats['final_penalty']} "
              f"({stats['improvement_percent']:.1f}%), "
              f"Time: {stats['elapsed_time']:.1f}s")

    print()

    # ------------------------------------------------------------------
    # SCHC VARIANTS x LC VALUES
    # ------------------------------------------------------------------
    for variant in VARIANTS:
        for lc in LC_VALUES:
            print(f"  Testing SCHC-{variant} (Lc={lc}):")

            for run in range(1, NUM_RUNS + 1):
                completed += 1
                elapsed   = time.time() - total_start
                eta_h     = (elapsed / completed) * (TOTAL_RUNS - completed) / 3600

                print(f"    Run {run}/{NUM_RUNS} [{completed}/{TOTAL_RUNS}] "
                      f"(ETA: {eta_h:.1f}h)...", end=" ", flush=True)

                schc = SCHC(
                    instance_data=instance,
                    Lc=lc,
                    variant=variant,
                    max_idle_iterations=MAX_IDLE_SCHC,
                    random_seed=run
                )
                _, stats = schc.optimize(baseline, verbose=False)

                csv_writer.writerow([
                    instance_name, f'SCHC-{variant}', lc, run,
                    baseline_penalty, stats['final_penalty'],
                    stats['improvement'], stats['improvement_percent'],
                    stats['iterations'], stats['bound_updates'],
                    stats['elapsed_time']
                ])

                result = {
                    'instance': instance_name,
                    'algorithm': f'SCHC-{variant}',
                    'lc': lc, 'run': run,
                    'baseline': baseline_penalty,
                    'final': stats['final_penalty'],
                    'improvement_pct': stats['improvement_percent'],
                    'iterations': stats['iterations'],
                    'bound_updates': stats['bound_updates'],
                    'time': stats['elapsed_time'],
                    'penalty_history': stats['penalty_history']
                }
                all_results.append(result)
                by_lc_variant[f'SCHC-{variant}-{lc}'].append(result)
                results_by_variant_lc[variant][lc].append(result)

                print(f"{baseline_penalty} → {stats['final_penalty']} "
                      f"({stats['improvement_percent']:.1f}%), "
                      f"Updates: {stats['bound_updates']}, "
                      f"Time: {stats['elapsed_time']:.1f}s")

            print()

    save_lc_comparison_plot(instance_name, results_by_variant_lc)
    save_checkpoint(f"Completed {instance_name}")

csv_file.close()
total_elapsed = time.time() - total_start
save_checkpoint(f"All instances complete - {total_elapsed / 3600:.2f}h")


# ============================================================================
# ANALYSIS
# ============================================================================

print("=" * 80)
print("ANALYSIS: Lc SENSITIVITY BY VARIANT")
print("=" * 80)
print()

for variant in VARIANTS:
    print(f"SCHC-{variant} - Lc Sensitivity:")
    print(f"{'Lc':<6} {'Avg Final':>10} {'Avg %':>8} {'StdDev':>8} "
          f"{'Best':>6} {'Worst':>6} {'AvgUpd':>8} {'AvgTime':>9}")
    print("-" * 72)

    for lc in LC_VALUES:
        key = f'SCHC-{variant}-{lc}'
        if key not in by_lc_variant:
            continue
        results = by_lc_variant[key]
        finals   = [r['final'] for r in results]
        pcts     = [r['improvement_pct'] for r in results]
        updates  = [r['bound_updates'] for r in results]
        times    = [r['time'] for r in results]

        avg_f, std_f, best_f, worst_f = compute_stats(finals)
        avg_pct  = sum(pcts) / len(pcts)
        avg_upd  = sum(updates) / len(updates)
        avg_time = sum(times) / len(times)

        print(f"{lc:<6} {avg_f:>10.1f} {avg_pct:>7.1f}% {std_f:>8.1f} "
              f"{best_f:>6} {worst_f:>6} {avg_upd:>8.0f} {avg_time:>8.1f}s")

    print()

print("=" * 80)
print()


# ============================================================================
# OPTIMAL Lc IDENTIFICATION
# ============================================================================

print("=" * 80)
print("OPTIMAL Lc IDENTIFICATION")
print("=" * 80)
print()

variant_optima = {}

for variant in VARIANTS:
    best_lc  = None
    best_avg = float('inf')
    lc_data  = []

    for lc in LC_VALUES:
        key = f'SCHC-{variant}-{lc}'
        if key in by_lc_variant:
            results = by_lc_variant[key]
            avg = sum(r['final'] for r in results) / len(results)
            lc_data.append((lc, avg))
            if avg < best_avg:
                best_avg = avg
                best_lc  = lc

    variant_optima[variant] = {'lc': best_lc, 'avg': best_avg}

    print(f"SCHC-{variant}:  Optimal Lc = {best_lc}  (avg penalty: {best_avg:.1f})")
    for lc, avg in lc_data:
        marker = "  ☆" if lc == best_lc else "   "
        diff   = avg - best_avg
        print(f"  {marker} Lc={lc:>4}: {avg:6.1f}  ({diff:+5.1f} from optimal)")
    print()

print("=" * 80)
print()


# ============================================================================
# VARIANT COMPARISON AT OPTIMAL Lc
# ============================================================================

print("=" * 80)
print("VARIANT COMPARISON AT OPTIMAL Lc")
print("=" * 80)
print()

hc_results = by_lc_variant.get('HC', [])
hc_avg     = sum(r['final'] for r in hc_results) / len(hc_results) if hc_results else 0

print(f"{'Algorithm':<14} {'Optimal Lc':>11} {'Avg Penalty':>12} {'vs HC':>10}")
print("-" * 52)
print(f"{'HC':14} {'N/A':>11} {hc_avg:>12.1f} {'(baseline)':>10}")

for variant in VARIANTS:
    lc  = variant_optima[variant]['lc']
    avg = variant_optima[variant]['avg']
    vs_hc = avg - hc_avg
    print(f"SCHC-{variant:<8} {lc:>11} {avg:>12.1f} {vs_hc:>+10.1f}")

best_variant = min(variant_optima.items(), key=lambda x: x[1]['avg'])
print()
print(f"OVERALL BEST: SCHC-{best_variant[0]} "
      f"with Lc={best_variant[1]['lc']} "
      f"(avg penalty: {best_variant[1]['avg']:.1f})")
print()
print("=" * 80)
print()


# ============================================================================
# SCALING CONTEXT NOTE
# ============================================================================

print("=" * 80)
print("LC SCALING CONTEXT")
print("=" * 80)
print()
print("Previous sprint optimal Lc (pre-fix, all variant only valid):")
print("  SCHC-all: ~150  (was correctly implemented)")
print("  SCHC-acp: undefined  (was Lc-insensitive due to bug)")
print("  SCHC-imp: undefined  (improvement trigger never fired due to bug)")
print()
print("New sprint optimal Lc (post-fix):")
for variant in VARIANTS:
    lc  = variant_optima[variant]['lc']
    avg = variant_optima[variant]['avg']
    print(f"  SCHC-{variant}: {lc}  (avg: {avg:.1f})")
print()
print("If acp or imp optimal Lc has shifted significantly from 'all',")
print("a medium Lc sweep is warranted before the final full test.")
print("=" * 80)
print()


# ============================================================================
# PLOTS AND SUMMARY
# ============================================================================

print("Generating plots...")
save_aggregate_plot(by_lc_variant)
save_scaling_context_plot(variant_optima, hc_avg)

print()
print("=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
print(f"Total runtime: {total_elapsed / 3600:.2f} hours ({total_elapsed / 60:.1f} minutes)")
print(f"Total runs completed: {completed}")
print(f"Average time per run: {total_elapsed / completed:.1f}s")
print()
print(f"Results saved to: {RUN_DIR}")
print(f"Summary CSV:      {summary_csv_path}")
print(f"Checkpoint log:   {CHECKPOINT_FILE}")
print("=" * 80)