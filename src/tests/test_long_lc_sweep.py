'''
Comprehensive Lc sensitivity analysis on long instances.
Tests Lc=[500, 750, 1000] to determine optimal Lc at large scale
and validate scaling hypothesis.

EXTENDED RUN CONFIGURATION:
- 5 instances × 3 SCHC variants × 3 Lc values × 5 runs = 225 SCHC runs
- 5 instances × 1 HC baseline × 5 runs = 25 HC runs
- Total: 250 runs (~30-35 hours)
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

# Long instances
INSTANCES = [
    f'data/inrc1/INRC1_long{i:02d}.json' for i in range(1, 6)
]

# SCHC variants
VARIANTS = ['all', 'acp', 'imp']

# Lc values - TEST SCALING HYPOTHESIS
# Medium optimal = 500 (868 assignments)
# Long = 1680 assignments (1.94× medium)
# Testing: 500 (baseline), 750 (1.5× medium), 1000 (2× medium)
LC_VALUES = [500, 750, 1000]

# Runs per configuration
NUM_RUNS = 5

# Convergence limits
MAX_IDLE_HC = 2000
MAX_IDLE_SCHC = 10000

# Output directory
OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR = OUTPUT_DIR / f'long_lc_sweep_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

# Progress checkpoint file
CHECKPOINT_FILE = RUN_DIR / 'checkpoint.txt'

print("="*80)
print("LONG INSTANCES - COMPREHENSIVE Lc SENSITIVITY ANALYSIS")
print("="*80)
print(f"Testing {len(INSTANCES)} long instances")
print(f"SCHC variants: {VARIANTS}")
print(f"Lc values: {LC_VALUES}")
print(f"Runs per configuration: {NUM_RUNS}")
print()
print("SCALING HYPOTHESIS TEST:")
print(f"  Sprint (280 assignments):  Optimal Lc ≈ 100-150")
print(f"  Medium (868 assignments):  Optimal Lc = 500")
print(f"  Long (1680 assignments):   Optimal Lc = ? (testing 500/750/1000)")
print()
print(f"SCHC runs: {len(INSTANCES)} × {len(VARIANTS)} × {len(LC_VALUES)} × {NUM_RUNS} = {len(INSTANCES) * len(VARIANTS) * len(LC_VALUES) * NUM_RUNS}")
print(f"HC runs: {len(INSTANCES)} × {NUM_RUNS} = {len(INSTANCES) * NUM_RUNS}")
print(f"Total runs: {len(INSTANCES) * (len(VARIANTS) * len(LC_VALUES) + 1) * NUM_RUNS}")
print()
print(f"Output directory: {RUN_DIR}")
print()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_checkpoint(message):
    '''Save progress checkpoint.'''
    with open(CHECKPOINT_FILE, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")


def save_lc_comparison_plot(instance_name, variant, results_by_lc):
    '''Save convergence plot comparing different Lc values for one variant.'''
    if not HAS_MATPLOTLIB:
        return
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = {500: 'blue', 750: 'green', 1000: 'red'}
    
    for lc in sorted(results_by_lc.keys()):
        results = results_by_lc[lc]
        
        # Plot all runs with transparency
        for result in results:
            history = result['penalty_history']
            iterations = list(range(0, len(history) * 10, 10))
            ax.plot(iterations, history, alpha=0.3, color=colors[lc], linewidth=1)
        
        # Plot average
        max_len = max(len(r['penalty_history']) for r in results)
        avg_history = []
        for i in range(max_len):
            values = [r['penalty_history'][i] for r in results 
                     if i < len(r['penalty_history'])]
            if values:
                avg_history.append(sum(values) / len(values))
        
        iterations = list(range(0, len(avg_history) * 10, 10))
        ax.plot(iterations, avg_history, color=colors[lc], 
               linewidth=3, label=f'Lc={lc}')
    
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('Penalty', fontsize=12)
    ax.set_title(f'{instance_name} - SCHC-{variant} Lc Comparison', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    filename = f'{instance_name}_SCHC-{variant}_lc_comparison.png'
    plt.savefig(RUN_DIR / filename, dpi=150, bbox_inches='tight')
    plt.close()


def save_aggregate_lc_plot(by_lc_variant):
    '''Save aggregate comparison of Lc values across all instances.'''
    if not HAS_MATPLOTLIB:
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Long Instances - Lc Sensitivity Analysis', 
                fontsize=16, fontweight='bold')
    
    variants = ['all', 'acp', 'imp']
    colors = {500: 'blue', 750: 'green', 1000: 'red'}
    
    for idx, variant in enumerate(variants):
        ax = axes[idx]
        
        lc_avgs = []
        lc_stds = []
        lc_labels = []
        
        for lc in sorted(LC_VALUES):
            key = f'SCHC-{variant}-{lc}'
            if key in by_lc_variant:
                results = by_lc_variant[key]
                finals = [r['final'] for r in results]
                avg = sum(finals) / len(finals)
                std = (sum((x - avg)**2 for x in finals) / len(finals))**0.5
                
                lc_avgs.append(avg)
                lc_stds.append(std)
                lc_labels.append(lc)
        
        # Bar plot with error bars
        x = range(len(lc_labels))
        bars = ax.bar(x, lc_avgs, color=[colors[lc] for lc in lc_labels], 
                     alpha=0.7, yerr=lc_stds, capsize=5)
        
        ax.set_xlabel('Lc Value', fontsize=11)
        ax.set_ylabel('Average Final Penalty', fontsize=11)
        ax.set_title(f'SCHC-{variant}', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(lc_labels)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, (v, s) in enumerate(zip(lc_avgs, lc_stds)):
            ax.text(i, v + s + max(lc_avgs)*0.02, f'{v:.1f}', 
                   ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(RUN_DIR / 'aggregate_lc_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()


def save_scaling_analysis_plot(sprint_data, medium_data, long_data):
    '''Create plot showing Lc scaling across problem sizes.'''
    if not HAS_MATPLOTLIB:
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('SCHC Lc Scaling Analysis: Sprint → Medium → Long', 
                fontsize=16, fontweight='bold')
    
    # Plot 1: Optimal Lc vs Problem Size
    problem_sizes = [280, 868, 1680]  # Sprint, Medium, Long assignments
    size_labels = ['Sprint\n(280)', 'Medium\n(868)', 'Long\n(1680)']
    
    for variant in ['all', 'imp']:
        optimal_lcs = [
            sprint_data[variant]['optimal_lc'],
            medium_data[variant]['optimal_lc'],
            long_data[variant]['optimal_lc']
        ]
        
        ax1.plot(problem_sizes, optimal_lcs, marker='o', markersize=10, 
                linewidth=2, label=f'SCHC-{variant}')
    
    ax1.set_xlabel('Problem Size (assignments)', fontsize=12)
    ax1.set_ylabel('Optimal Lc', fontsize=12)
    ax1.set_title('Optimal Lc Scaling', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Quality Improvement vs Problem Size
    for variant in ['all', 'imp']:
        improvements = [
            sprint_data[variant]['improvement_pct'],
            medium_data[variant]['improvement_pct'],
            long_data[variant]['improvement_pct']
        ]
        
        ax2.plot(problem_sizes, improvements, marker='s', markersize=10, 
                linewidth=2, label=f'SCHC-{variant}')
    
    ax2.set_xlabel('Problem Size (assignments)', fontsize=12)
    ax2.set_ylabel('Improvement % (from baseline)', fontsize=12)
    ax2.set_title('Quality Degradation with Scale', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(RUN_DIR / 'scaling_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()


# ============================================================================
# MAIN TESTING LOOP
# ============================================================================

all_results = []
instance_details = []

# CSV file
summary_csv_path = RUN_DIR / 'summary.csv'
csv_file = open(summary_csv_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'Instance', 'Algorithm', 'Lc', 'Run', 'Nurses', 'Days', 'Baseline', 'Final', 
    'Improvement', 'Improvement_Pct', 'Iterations', 'Bound_Updates', 'Time'
])

total_start_time = time.time()
completed_runs = 0
total_runs = len(INSTANCES) * (len(VARIANTS) * len(LC_VALUES) + 1) * NUM_RUNS

save_checkpoint(f"Starting test - {total_runs} total runs")

for instance_path in INSTANCES:
    if not Path(instance_path).exists():
        print(f"CAUTION Skipping {instance_path}")
        save_checkpoint(f"Skipped {instance_path} - not found")
        continue
    
    instance_name = Path(instance_path).stem
    
    print("="*80)
    print(f"TESTING: {instance_name}")
    print("="*80)
    save_checkpoint(f"Started {instance_name}")
    
    instance_start = time.time()
    
    # Load instance
    try:
        instance = load_instance(instance_path)
        n_nurses = len(instance['nurses'])
        n_days = instance['period']
        print(f"Loaded: {instance['name']} ({n_nurses} nurses, {n_days} days)")
        
        instance_details.append({
            'name': instance_name,
            'nurses': n_nurses,
            'days': n_days
        })
    except Exception as e:
        print(f"ERROR loading: {e}")
        save_checkpoint(f"ERROR loading {instance_name}: {e}")
        continue
    
    # Generate baseline
    baseline = greedy_constructor(instance)
    baseline_penalty = evaluate_solution(baseline, instance)
    print(f"Baseline penalty: {baseline_penalty}")
    print()
    
    # Store results by variant and Lc for plotting
    results_by_variant_lc = defaultdict(lambda: defaultdict(list))
    
    # Test HC baseline
    print("  Testing HC (baseline):")
    for run in range(1, NUM_RUNS + 1):
        completed_runs += 1
        elapsed_total = time.time() - total_start_time
        eta_seconds = (elapsed_total / completed_runs) * (total_runs - completed_runs)
        eta_hours = eta_seconds / 3600
        
        print(f"    Run {run}/{NUM_RUNS} [{completed_runs}/{total_runs}] "
              f"(ETA: {eta_hours:.1f}h)...", end=" ", flush=True)
        
        hc = HillClimbing(
            instance_data=instance,
            max_idle_iterations=MAX_IDLE_HC,
            random_seed=run
        )
        
        best_solution, stats = hc.optimize(baseline, verbose=False)
        
        csv_writer.writerow([
            instance_name, 'HC', 0, run, n_nurses, n_days, baseline_penalty,
            stats['final_penalty'], stats['improvement'], 
            stats['improvement_percent'], stats['iterations'], 
            0, stats['elapsed_time']
        ])
        
        all_results.append({
            'instance': instance_name,
            'algorithm': 'HC',
            'lc': 0,
            'run': run,
            'nurses': n_nurses,
            'days': n_days,
            'baseline': baseline_penalty,
            'final': stats['final_penalty'],
            'improvement_pct': stats['improvement_percent'],
            'iterations': stats['iterations'],
            'time': stats['elapsed_time'],
            'penalty_history': stats['penalty_history']
        })
        
        print(f"{baseline_penalty} → {stats['final_penalty']} "
              f"({stats['improvement_percent']:.1f}%), Time: {stats['elapsed_time']:.1f}s")
    
    print()
    
    # Test each SCHC variant with each Lc value
    for variant in VARIANTS:
        for lc in LC_VALUES:
            print(f"  Testing SCHC-{variant} (Lc={lc}):")
            
            for run in range(1, NUM_RUNS + 1):
                completed_runs += 1
                elapsed_total = time.time() - total_start_time
                eta_seconds = (elapsed_total / completed_runs) * (total_runs - completed_runs)
                eta_hours = eta_seconds / 3600
                
                print(f"    Run {run}/{NUM_RUNS} [{completed_runs}/{total_runs}] "
                      f"(ETA: {eta_hours:.1f}h)...", end=" ", flush=True)
                
                schc = SCHC(
                    instance_data=instance,
                    Lc=lc,
                    variant=variant,
                    max_idle_iterations=MAX_IDLE_SCHC,
                    random_seed=run
                )
                
                best_solution, stats = schc.optimize(baseline, verbose=False)
                
                csv_writer.writerow([
                    instance_name, f'SCHC-{variant}', lc, run, n_nurses, n_days,
                    baseline_penalty, stats['final_penalty'], stats['improvement'],
                    stats['improvement_percent'], stats['iterations'],
                    stats['bound_updates'], stats['elapsed_time']
                ])
                
                result = {
                    'instance': instance_name,
                    'algorithm': f'SCHC-{variant}',
                    'lc': lc,
                    'run': run,
                    'nurses': n_nurses,
                    'days': n_days,
                    'baseline': baseline_penalty,
                    'final': stats['final_penalty'],
                    'improvement_pct': stats['improvement_percent'],
                    'iterations': stats['iterations'],
                    'bound_updates': stats['bound_updates'],
                    'time': stats['elapsed_time'],
                    'penalty_history': stats['penalty_history']
                }
                all_results.append(result)
                results_by_variant_lc[variant][lc].append(result)
                
                print(f"{baseline_penalty} → {stats['final_penalty']} "
                      f"({stats['improvement_percent']:.1f}%), "
                      f"Updates: {stats['bound_updates']}, "
                      f"Time: {stats['elapsed_time']:.1f}s")
            
            print()
    
    # Save per-variant Lc comparison plots
    for variant in VARIANTS:
        save_lc_comparison_plot(instance_name, variant, 
                                results_by_variant_lc[variant])
    
    instance_elapsed = time.time() - instance_start
    save_checkpoint(f"Completed {instance_name} in {instance_elapsed/60:.1f} minutes")
    print(f"{instance_name} complete in {instance_elapsed/60:.1f} minutes")
    print()

csv_file.close()

total_elapsed = time.time() - total_start_time
save_checkpoint(f"Testing complete - {total_elapsed/3600:.2f} hours")


# ============================================================================
# COMPREHENSIVE ANALYSIS
# ============================================================================

print("="*80)
print("ANALYSIS: Lc SENSITIVITY BY VARIANT")
print("="*80)
print()

# Group results
by_lc_variant = defaultdict(list)
for result in all_results:
    if result['algorithm'] == 'HC':
        by_lc_variant['HC'].append(result)
    else:
        key = f"{result['algorithm']}-{result['lc']}"
        by_lc_variant[key].append(result)

# Analysis by variant
for variant in VARIANTS:
    print(f"SCHC-{variant} - Lc Sensitivity:")
    print(f"{'Lc':<6} {'Avg Final':>10} {'Avg %':>8} {'StdDev':>8} "
          f"{'Best':>6} {'Worst':>6} {'AvgUpd':>8} {'AvgTime':>8}")
    print("-"*70)
    
    for lc in sorted(LC_VALUES):
        key = f'SCHC-{variant}-{lc}'
        if key not in by_lc_variant:
            continue
        
        results = by_lc_variant[key]
        finals = [r['final'] for r in results]
        improvements = [r['improvement_pct'] for r in results]
        updates = [r['bound_updates'] for r in results]
        times = [r['time'] for r in results]
        
        avg_final = sum(finals) / len(finals)
        avg_pct = sum(improvements) / len(improvements)
        stddev = (sum((x - avg_final)**2 for x in finals) / len(finals))**0.5
        best = min(finals)
        worst = max(finals)
        avg_upd = sum(updates) / len(updates)
        avg_time = sum(times) / len(times)
        
        print(f"{lc:<6} {avg_final:>10.1f} {avg_pct:>7.1f}% {stddev:>8.1f} "
              f"{best:>6} {worst:>6} {avg_upd:>8.0f} {avg_time:>7.1f}s")
    
    print()

print("="*80)
print()


# ============================================================================
# OPTIMAL Lc IDENTIFICATION
# ============================================================================

print("="*80)
print("OPTIMAL Lc IDENTIFICATION (LONG INSTANCES)")
print("="*80)
print()

long_optimal_data = {}

for variant in VARIANTS:
    print(f"SCHC-{variant}:")
    
    best_lc = None
    best_avg = float('inf')
    
    lc_results = []
    for lc in sorted(LC_VALUES):
        key = f'SCHC-{variant}-{lc}'
        if key in by_lc_variant:
            results = by_lc_variant[key]
            finals = [r['final'] for r in results]
            improvements = [r['improvement_pct'] for r in results]
            avg = sum(finals) / len(finals)
            avg_pct = sum(improvements) / len(improvements)
            lc_results.append((lc, avg, avg_pct))
            
            if avg < best_avg:
                best_avg = avg
                best_lc = lc
    
    long_optimal_data[variant] = {
        'optimal_lc': best_lc,
        'avg_penalty': best_avg,
        'improvement_pct': next(pct for lc, avg, pct in lc_results if lc == best_lc)
    }
    
    print(f"  Optimal Lc: {best_lc} (avg penalty: {best_avg:.1f})")
    
    # Show relative performance
    for lc, avg, avg_pct in lc_results:
        diff = avg - best_avg
        marker = "☆" if lc == best_lc else "  "
        print(f"  {marker} Lc={lc:4d}: {avg:6.1f} ({diff:+5.1f} from optimal, {avg_pct:.1f}% improvement)")
    
    print()

print("="*80)
print()


# ============================================================================
# VARIANT COMPARISON AT OPTIMAL Lc
# ============================================================================

print("="*80)
print("VARIANT COMPARISON (Each at its optimal Lc)")
print("="*80)
print()

variant_optima = {}
for variant in VARIANTS:
    best_lc = None
    best_avg = float('inf')
    
    for lc in LC_VALUES:
        key = f'SCHC-{variant}-{lc}'
        if key in by_lc_variant:
            results = by_lc_variant[key]
            avg = sum(r['final'] for r in results) / len(results)
            if avg < best_avg:
                best_avg = avg
                best_lc = lc
    
    variant_optima[variant] = (best_lc, best_avg)

print(f"{'Variant':<12} {'Optimal Lc':>11} {'Avg Penalty':>12}")
print("-"*40)
for variant in VARIANTS:
    lc, avg = variant_optima[variant]
    print(f"SCHC-{variant:<6} {lc:>11} {avg:>12.1f}")

# Determine overall best
best_variant = min(variant_optima.items(), key=lambda x: x[1][1])
print()
print(f"OVERALL BEST: SCHC-{best_variant[0]} with Lc={best_variant[1][0]} "
      f"(avg penalty: {best_variant[1][1]:.1f})")
print()
print("="*80)
print()


# ============================================================================
# SCALING ANALYSIS
# ============================================================================

print("="*80)
print("SCALING ANALYSIS: SPRINT → MEDIUM → LONG")
print("="*80)
print()

# Historical data (from previous tests)
sprint_optimal_data = {
    'all': {'optimal_lc': 150, 'avg_penalty': 57.6, 'improvement_pct': 77.3},
    'imp': {'optimal_lc': 150, 'avg_penalty': 59.5, 'improvement_pct': 76.6}
}

medium_optimal_data = {
    'all': {'optimal_lc': 500, 'avg_penalty': 270.1, 'improvement_pct': 44.6},
    'imp': {'optimal_lc': 500, 'avg_penalty': 269.4, 'improvement_pct': 44.7}
}

print("Lc SCALING:")
print(f"{'Scale':<10} {'Size':>6} {'SCHC-all Lc':>12} {'SCHC-imp Lc':>12}")
print("-"*50)
print(f"{'Sprint':<10} {280:>6} {sprint_optimal_data['all']['optimal_lc']:>12} "
      f"{sprint_optimal_data['imp']['optimal_lc']:>12}")
print(f"{'Medium':<10} {868:>6} {medium_optimal_data['all']['optimal_lc']:>12} "
      f"{medium_optimal_data['imp']['optimal_lc']:>12}")
print(f"{'Long':<10} {1680:>6} {long_optimal_data['all']['optimal_lc']:>12} "
      f"{long_optimal_data['imp']['optimal_lc']:>12}")
print()

print("QUALITY DEGRADATION:")
print(f"{'Scale':<10} {'SCHC-all %':>12} {'SCHC-imp %':>12}")
print("-"*40)
print(f"{'Sprint':<10} {sprint_optimal_data['all']['improvement_pct']:>11.1f}% "
      f"{sprint_optimal_data['imp']['improvement_pct']:>11.1f}%")
print(f"{'Medium':<10} {medium_optimal_data['all']['improvement_pct']:>11.1f}% "
      f"{medium_optimal_data['imp']['improvement_pct']:>11.1f}%")
print(f"{'Long':<10} {long_optimal_data['all']['improvement_pct']:>11.1f}% "
      f"{long_optimal_data['imp']['improvement_pct']:>11.1f}%")
print()

# Calculate Lc/Size ratios
print("Lc/SIZE RATIO ANALYSIS:")
print(f"{'Scale':<10} {'Lc/Size (all)':>15} {'Lc/Size (imp)':>15}")
print("-"*45)
print(f"{'Sprint':<10} {sprint_optimal_data['all']['optimal_lc']/280:>15.3f} "
      f"{sprint_optimal_data['imp']['optimal_lc']/280:>15.3f}")
print(f"{'Medium':<10} {medium_optimal_data['all']['optimal_lc']/868:>15.3f} "
      f"{medium_optimal_data['imp']['optimal_lc']/868:>15.3f}")
print(f"{'Long':<10} {long_optimal_data['all']['optimal_lc']/1680:>15.3f} "
      f"{long_optimal_data['imp']['optimal_lc']/1680:>15.3f}")

print("="*80)
print()


# ============================================================================
# SAVE PLOTS
# ============================================================================

print("Generating plots...")
save_aggregate_lc_plot(by_lc_variant)
print("Aggregate Lc comparison plot saved")

save_scaling_analysis_plot(sprint_optimal_data, medium_optimal_data, long_optimal_data)
print("Scaling analysis plot saved")
print()


# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("="*80)
print("TESTING COMPLETE")
print("="*80)
print()
print(f"Total runtime: {total_elapsed/3600:.2f} hours ({total_elapsed/60:.1f} minutes)")
print(f"Total runs completed: {completed_runs}")
print(f"Average time per run: {total_elapsed/completed_runs:.1f}s")
print()
print(f"All results saved to: {RUN_DIR}")
print(f"Summary CSV: {summary_csv_path}")
print(f"Per-instance plots: {RUN_DIR}/*_lc_comparison.png")
print(f"Aggregate plot: {RUN_DIR}/aggregate_lc_comparison.png")
print(f"Scaling analysis: {RUN_DIR}/scaling_analysis.png")
print(f"Checkpoint log: {CHECKPOINT_FILE}")
print()
print("Scalability analysis complete")
print()
print("="*80)