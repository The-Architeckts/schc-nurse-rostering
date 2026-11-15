'''
Comprehensive testing of all SCHC variants on medium instances.
Tests HC baseline + SCHC-all, SCHC-acp, SCHC-imp to identify
which variant scales best to larger problem sizes.
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
    print("Warning: matplotlib not available")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Medium instances (all available)
INSTANCES = [
    f'data/inrc1/INRC1_medium{i:02d}.json' for i in range(1, 6)
]

# Test HC baseline + all 3 SCHC variants
ALGORITHMS = ['HC', 'SCHC-all', 'SCHC-acp', 'SCHC-imp']

# Lc value (use optimal from sprint testing)
LC_VALUE = 100

# Runs per configuration
NUM_RUNS = 10

# Convergence limits (increased for larger instances)
MAX_IDLE_HC = 2000      # Double sprint value
MAX_IDLE_SCHC = 10000   # Double sprint value

# Output directory
OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR = OUTPUT_DIR / f'medium_batch_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

print("="*80)
print("MEDIUM INSTANCES - COMPREHENSIVE SCHC VARIANT TESTING")
print("="*80)
print(f"Testing {len(INSTANCES)} medium instances")
print(f"Algorithms: {ALGORITHMS}")
print(f"Lc value: {LC_VALUE}")
print(f"Runs per configuration: {NUM_RUNS}")
print(f"Total runs: {len(INSTANCES) * len(ALGORITHMS) * NUM_RUNS}")
print(f"Output directory: {RUN_DIR}")
print()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_convergence_plot_comparison(instance_name, results_by_algo):
    '''Save comparison plot for all algorithms on one instance.'''
    if not HAS_MATPLOTLIB:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{instance_name} - Algorithm Comparison', fontsize=16, fontweight='bold')
    
    colors = {
        'HC': 'blue',
        'SCHC-all': 'green', 
        'SCHC-acp': 'orange',
        'SCHC-imp': 'red'
    }
    
    algo_list = ['HC', 'SCHC-all', 'SCHC-acp', 'SCHC-imp']
    
    for idx, algo in enumerate(algo_list):
        if algo not in results_by_algo:
            continue
        
        ax = axes[idx // 2, idx % 2]
        results = results_by_algo[algo]
        
        # Plot all runs
        for result in results:
            history = result['penalty_history']
            iterations = list(range(0, len(history) * 10, 10))
            ax.plot(iterations, history, alpha=0.3, color=colors[algo], linewidth=1)
        
        # Plot average
        max_len = max(len(r['penalty_history']) for r in results)
        avg_history = []
        for i in range(max_len):
            values = [r['penalty_history'][i] for r in results 
                     if i < len(r['penalty_history'])]
            if values:
                avg_history.append(sum(values) / len(values))
        
        iterations = list(range(0, len(avg_history) * 10, 10))
        ax.plot(iterations, avg_history, color=colors[algo], 
               linewidth=3, label='Average')
        
        ax.set_title(f'{algo}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Iteration', fontsize=10)
        ax.set_ylabel('Penalty', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    
    filename = f'{instance_name}_comparison.png'
    filepath = RUN_DIR / filename
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()


def save_aggregate_comparison_plot(by_instance):
    '''Save aggregate comparison across all instances.'''
    if not HAS_MATPLOTLIB:
        return
    
    instances = sorted(by_instance.keys())
    algorithms = ['HC', 'SCHC-all', 'SCHC-acp', 'SCHC-imp']
    
    # Prepare data
    data = {algo: [] for algo in algorithms}
    
    for instance in instances:
        for algo in algorithms:
            if algo in by_instance[instance]:
                results = by_instance[instance][algo]
                avg = sum(r['final'] for r in results) / len(results)
                data[algo].append(avg)
            else:
                data[algo].append(None)
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Average penalty by instance
    x = range(len(instances))
    width = 0.2
    
    for i, algo in enumerate(algorithms):
        offset = (i - 1.5) * width
        values = [v if v is not None else 0 for v in data[algo]]
        ax1.bar([p + offset for p in x], values, width, label=algo)
    
    ax1.set_xlabel('Instance', fontsize=12)
    ax1.set_ylabel('Average Final Penalty', fontsize=12)
    ax1.set_title('Average Penalty by Instance', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([inst.split('_')[-1] for inst in instances], rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Algorithm comparison (overall average)
    overall_avgs = []
    for algo in algorithms:
        valid_values = [v for v in data[algo] if v is not None]
        if valid_values:
            overall_avgs.append(sum(valid_values) / len(valid_values))
        else:
            overall_avgs.append(0)
    
    colors = ['blue', 'green', 'orange', 'red']
    ax2.bar(algorithms, overall_avgs, color=colors, alpha=0.7)
    ax2.set_ylabel('Average Final Penalty', fontsize=12)
    ax2.set_title('Overall Algorithm Performance', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(overall_avgs):
        ax2.text(i, v + max(overall_avgs)*0.02, f'{v:.1f}', 
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(RUN_DIR / 'aggregate_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()


# ============================================================================
# MAIN TESTING LOOP
# ============================================================================

all_results = []
instance_details = []  # Store instance size info

# CSV file
summary_csv_path = RUN_DIR / 'summary.csv'
csv_file = open(summary_csv_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'Instance', 'Algorithm', 'Run', 'Nurses', 'Days', 'Baseline', 'Final', 
    'Improvement', 'Improvement_Pct', 'Iterations', 'Bound_Updates', 'Time'
])

total_start_time = time.time()
completed_runs = 0
total_runs = sum(1 for inst in INSTANCES if Path(inst).exists()) * len(ALGORITHMS) * NUM_RUNS

for instance_path in INSTANCES:
    if not Path(instance_path).exists():
        print(f"CAUTION Skipping {instance_path} (file not found)")
        continue
    
    instance_name = Path(instance_path).stem
    
    print("="*80)
    print(f"TESTING: {instance_name}")
    print("="*80)
    
    instance_start_time = time.time()
    
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
        continue
    
    # Generate baseline
    baseline = greedy_constructor(instance)
    baseline_penalty = evaluate_solution(baseline, instance)
    print(f"Baseline penalty: {baseline_penalty}")
    print()
    
    # Store results by algorithm for convergence plot
    results_by_algo = defaultdict(list)
    
    # Test each algorithm
    for algo in ALGORITHMS:
        print(f"  Testing {algo}:")
        
        for run in range(1, NUM_RUNS + 1):
            completed_runs += 1
            elapsed_total = time.time() - total_start_time
            eta_seconds = (elapsed_total / completed_runs) * (total_runs - completed_runs)
            eta_hours = eta_seconds / 3600
            
            print(f"    Run {run}/{NUM_RUNS} [{completed_runs}/{total_runs}] "
                  f"(ETA: {eta_hours:.1f}h)...", end=" ", flush=True)
            
            # Initialize algorithm
            if algo == 'HC':
                algorithm = HillClimbing(
                    instance_data=instance,
                    max_idle_iterations=MAX_IDLE_HC,
                    random_seed=run
                )
            else:
                variant = algo.split('-')[1]  # Extract 'all', 'acp', or 'imp'
                algorithm = SCHC(
                    instance_data=instance,
                    Lc=LC_VALUE,
                    variant=variant,
                    max_idle_iterations=MAX_IDLE_SCHC,
                    random_seed=run
                )
            
            # Optimize
            best_solution, stats = algorithm.optimize(baseline, verbose=False)
            
            # Write to CSV
            csv_writer.writerow([
                instance_name, algo, run, n_nurses, n_days,
                baseline_penalty, stats['final_penalty'],
                stats['improvement'], stats['improvement_percent'],
                stats['iterations'], stats.get('bound_updates', 0),
                stats['elapsed_time']
            ])
            
            # Store result
            result = {
                'instance': instance_name,
                'algorithm': algo,
                'run': run,
                'nurses': n_nurses,
                'days': n_days,
                'baseline': baseline_penalty,
                'final': stats['final_penalty'],
                'improvement_pct': stats['improvement_percent'],
                'iterations': stats['iterations'],
                'bound_updates': stats.get('bound_updates', 0),
                'time': stats['elapsed_time'],
                'penalty_history': stats['penalty_history']
            }
            all_results.append(result)
            results_by_algo[algo].append(result)
            
            print(f"{baseline_penalty} → {stats['final_penalty']} "
                  f"({stats['improvement_percent']:.1f}%), "
                  f"Time: {stats['elapsed_time']:.1f}s")
        
        print()
    
    # Save convergence comparison plot for this instance
    save_convergence_plot_comparison(instance_name, results_by_algo)
    
    instance_elapsed = time.time() - instance_start_time
    print(f"{instance_name} complete in {instance_elapsed/60:.1f} minutes")
    print()

csv_file.close()

total_elapsed = time.time() - total_start_time


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("="*80)
print("SUMMARY STATISTICS BY INSTANCE")
print("="*80)
print()

# Group by instance and algorithm
by_instance_algo = defaultdict(lambda: defaultdict(list))
for result in all_results:
    by_instance_algo[result['instance']][result['algorithm']].append(result)

print(f"{'Instance':<20} {'Nurses':>7} {'Days':>5} {'Algorithm':<12} "
      f"{'Best':>6} {'Worst':>6} {'Avg':>7} {'StdDev':>7} {'Avg%':>7}")
print("-"*95)

for detail in instance_details:
    instance_name = detail['name']
    first_row = True
    
    for algo in ALGORITHMS:
        if algo not in by_instance_algo[instance_name]:
            continue
        
        results = by_instance_algo[instance_name][algo]
        
        finals = [r['final'] for r in results]
        improvements = [r['improvement_pct'] for r in results]
        
        best = min(finals)
        worst = max(finals)
        avg = sum(finals) / len(finals)
        stddev = (sum((x - avg)**2 for x in finals) / len(finals))**0.5
        avg_pct = sum(improvements) / len(improvements)
        
        if first_row:
            print(f"{instance_name:<20} {detail['nurses']:>7} {detail['days']:>5} "
                  f"{algo:<12} {best:>6} {worst:>6} {avg:>7.1f} {stddev:>7.1f} {avg_pct:>6.1f}%")
            first_row = False
        else:
            print(f"{'':>33} {algo:<12} {best:>6} {worst:>6} {avg:>7.1f} "
                  f"{stddev:>7.1f} {avg_pct:>6.1f}%")
    
    print("-"*95)

print("="*80)
print()


# ============================================================================
# AGGREGATE COMPARISON
# ============================================================================

print("="*80)
print("AGGREGATE COMPARISON (ALL MEDIUM INSTANCES)")
print("="*80)
print()

by_algo = defaultdict(list)
for result in all_results:
    by_algo[result['algorithm']].append(result)

print(f"{'Algorithm':<12} {'Avg Final':>10} {'Avg%':>7} {'StdDev':>7} "
      f"{'Best':>6} {'Worst':>6} {'AvgIter':>8} {'AvgTime':>8}")
print("-"*75)

for algo in ALGORITHMS:
    if algo not in by_algo:
        continue
    
    results = by_algo[algo]
    
    finals = [r['final'] for r in results]
    improvements = [r['improvement_pct'] for r in results]
    iterations = [r['iterations'] for r in results]
    times = [r['time'] for r in results]
    
    avg_final = sum(finals) / len(finals)
    avg_pct = sum(improvements) / len(improvements)
    stddev = (sum((x - avg_final)**2 for x in finals) / len(finals))**0.5
    best = min(finals)
    worst = max(finals)
    avg_iter = sum(iterations) / len(iterations)
    avg_time = sum(times) / len(times)
    
    print(f"{algo:<12} {avg_final:>10.1f} {avg_pct:>6.1f}% {stddev:>7.1f} "
          f"{best:>6} {worst:>6} {avg_iter:>8.0f} {avg_time:>7.1f}s")

print("="*80)
print()


# ============================================================================
# ALGORITHM COMPARISON
# ============================================================================

print("="*80)
print("ALGORITHM HEAD-TO-HEAD COMPARISON")
print("="*80)
print()

# Check if we have any results
if 'HC' not in by_algo or len(by_algo['HC']) == 0:
    print("CAUTION No results available - testing failed or no instances loaded")
    print("="*80)
else:
    hc_results = by_algo['HC']
    hc_avg = sum(r['final'] for r in hc_results) / len(hc_results)

for algo in ['SCHC-all', 'SCHC-acp', 'SCHC-imp']:
    if algo not in by_algo:
        continue
    
    schc_results = by_algo[algo]
    schc_avg = sum(r['final'] for r in schc_results) / len(schc_results)
    
    diff = hc_avg - schc_avg
    
    # Win/loss
    wins = sum(1 for hc_r, schc_r in zip(hc_results, schc_results) 
               if schc_r['final'] < hc_r['final'])
    losses = sum(1 for hc_r, schc_r in zip(hc_results, schc_results) 
                 if schc_r['final'] > hc_r['final'])
    ties = len(hc_results) - wins - losses
    
    print(f"HC vs {algo}:")
    print(f"  Average: {hc_avg:.1f} vs {schc_avg:.1f} (Δ={diff:+.1f}, {abs(diff)/hc_avg*100:.1f}%)")
    print(f"  Win/Loss: {wins}W - {losses}L - {ties}T ({wins/len(hc_results)*100:.0f}% win rate)")
    
    if diff > 0:
        print(f"  O {algo} BETTER by {diff:.1f} penalties")
    elif diff < 0:
        print(f"  X HC BETTER by {abs(diff):.1f} penalties")
    else:
        print(f"  - TIE")
    print()

# SCHC variant comparison
print("SCHC VARIANT COMPARISON:")
print()

variant_pairs = [
    ('SCHC-all', 'SCHC-acp'),
    ('SCHC-all', 'SCHC-imp'),
    ('SCHC-acp', 'SCHC-imp')
]

for var1, var2 in variant_pairs:
    if var1 not in by_algo or var2 not in by_algo:
        continue
    
    results1 = by_algo[var1]
    results2 = by_algo[var2]
    
    avg1 = sum(r['final'] for r in results1) / len(results1)
    avg2 = sum(r['final'] for r in results2) / len(results2)
    
    diff = avg1 - avg2
    
    wins = sum(1 for r1, r2 in zip(results1, results2) if r2['final'] < r1['final'])
    losses = sum(1 for r1, r2 in zip(results1, results2) if r2['final'] > r1['final'])
    ties = len(results1) - wins - losses
    
    print(f"{var1} vs {var2}:")
    print(f"  Average: {avg1:.1f} vs {avg2:.1f} (Δ={diff:+.1f})")
    print(f"  Win/Loss: {wins}W - {losses}L - {ties}T")
    
    if wins > losses:
        print(f"  → {var2} BETTER")
    elif losses > wins:
        print(f"  → {var1} BETTER")
    else:
        print(f"  → TIE")
    print()

print("="*80)
print()


# ============================================================================
# SCALABILITY ANALYSIS
# ============================================================================

print("="*80)
print("SCALABILITY ANALYSIS")
print("="*80)
print()

print("Sprint vs Medium Comparison:")
print()

# Sprint results (from previous testing - you'll need to update these)
sprint_results = {
    'HC': {'avg': 65.3, 'avg_pct': 74.3, 'avg_time': 2.8},
    'SCHC-all': {'avg': 59.7, 'avg_pct': 77.0, 'avg_time': 9.6},
    'SCHC-acp': {'avg': 63.3, 'avg_pct': 75.6, 'avg_time': 7.0},
    'SCHC-imp': {'avg': 60.1, 'avg_pct': 76.8, 'avg_time': 9.6}
}

print(f"{'Algorithm':<12} {'Sprint Avg%':>12} {'Medium Avg%':>12} "
      f"{'Quality Δ':>10} {'Sprint Time':>12} {'Medium Time':>12} {'Time Δ':>8}")
print("-"*85)

for algo in ALGORITHMS:
    if algo not in by_algo:
        continue
    
    medium_pct = sum(r['improvement_pct'] for r in by_algo[algo]) / len(by_algo[algo])
    medium_time = sum(r['time'] for r in by_algo[algo]) / len(by_algo[algo])
    
    sprint_pct = sprint_results[algo]['avg_pct']
    sprint_time = sprint_results[algo]['avg_time']
    
    quality_diff = medium_pct - sprint_pct
    time_multiplier = medium_time / sprint_time
    
    print(f"{algo:<12} {sprint_pct:>11.1f}% {medium_pct:>11.1f}% "
          f"{quality_diff:>+9.1f}% {sprint_time:>11.1f}s {medium_time:>11.1f}s {time_multiplier:>7.1f}×")

print("="*80)
print()


# ============================================================================
# SAVE AGGREGATE PLOT
# ============================================================================

print("Generating aggregate comparison plot...")
save_aggregate_comparison_plot(by_instance_algo)
print("Aggregate plot saved")
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
print(f"Convergence plots: {RUN_DIR}/*_comparison.png")
print(f"Aggregate plot: {RUN_DIR}/aggregate_comparison.png")
print()
print("="*80)