'''
Batch testing of SCHC on multiple INRC-I instances.
Tests multiple Lc values and compares with HC baseline.
Automatically logs all results with timestamps and unique file names.
'''

import sys
from pathlib import Path
import time
import csv
from datetime import datetime
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.hill_climbing import HillClimbing
from algorithms.schc import SCHC_all
from constraints import evaluate_solution
from models import ShiftType

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available, skipping convergence plots")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Instances to test
INSTANCES = [f'data/inrc1/INRC1_sprint{i:02d}.json' for i in range(1, 11)]

# Lc values to test
LC_VALUES = [0, 50, 100, 150]  # CONFIGURE THIS

# Number of runs per instance per Lc
NUM_RUNS = 10

# HC/SCHC configuration
MAX_IDLE_HC = 1000
MAX_IDLE_SCHC = 5000

# Create output directory
OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

# Create timestamped subdirectory for this test run
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR = OUTPUT_DIR / f'schc_batch_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

print(f"Output directory: {RUN_DIR}")
print(f"Testing {len(INSTANCES)} instances")
print(f"Lc values: {LC_VALUES}")
print(f"Runs per instance per Lc: {NUM_RUNS}")
print(f"Total runs: {len(INSTANCES) * len(LC_VALUES) * NUM_RUNS}")
print()


# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

def save_convergence_plot(penalty_history, instance_name, lc_value, run_number):
    '''Save convergence plot with unique filename.'''
    if not HAS_MATPLOTLIB:
        return None
    
    plt.figure(figsize=(10, 6))
    iterations = list(range(0, len(penalty_history) * 10, 10))
    
    color = 'blue' if lc_value == 0 else 'green' if lc_value <= 75 else 'orange' if lc_value <= 125 else 'red'
    
    plt.plot(iterations, penalty_history, color=color, linewidth=2)
    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Penalty', fontsize=12)
    
    algo_name = f"HC (Lc={lc_value})" if lc_value == 0 else f"SCHC-all (Lc={lc_value})"
    plt.title(f'{instance_name} - {algo_name} - Run {run_number}', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Save with unique name
    filename = f'{instance_name}_Lc{lc_value:03d}_run{run_number:02d}.png'
    filepath = RUN_DIR / filename
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    return str(filepath)


def save_detailed_log(instance_name, lc_value, run_number, baseline_penalty, stats, operator_stats):
    '''Save detailed log file for this run.'''
    filename = f'{instance_name}_Lc{lc_value:03d}_run{run_number:02d}_detailed.txt'
    filepath = RUN_DIR / filename
    
    algo_name = "Hill Climbing" if lc_value == 0 else f"SCHC-all (Lc={lc_value})"
    
    with open(filepath, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"{algo_name.upper()} DETAILED RESULTS\n")
        f.write("="*80 + "\n")
        f.write(f"Instance: {instance_name}\n")
        f.write(f"Lc value: {lc_value}\n")
        f.write(f"Run: {run_number}\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")
        
        f.write("OPTIMIZATION RESULTS:\n")
        f.write("-"*80 + "\n")
        f.write(f"Initial penalty:    {baseline_penalty}\n")
        f.write(f"Final penalty:      {stats['final_penalty']}\n")
        f.write(f"Improvement:        {stats['improvement']} ({stats['improvement_percent']:.1f}%)\n")
        f.write(f"Iterations:         {stats['iterations']}\n")
        f.write(f"Accepted moves:     {stats['accepted_moves']}\n")
        f.write(f"Rejected moves:     {stats['rejected_moves']}\n")
        f.write(f"Acceptance rate:    {stats['accepted_moves']/(stats['accepted_moves']+stats['rejected_moves'])*100:.2f}%\n")
        
        if lc_value > 0:
            f.write(f"Bound updates:      {stats['bound_updates']}\n")
        
        f.write(f"Elapsed time:       {stats['elapsed_time']:.2f}s\n")
        f.write("\n")
        
        f.write("OPERATOR STATISTICS:\n")
        f.write("-"*80 + "\n")
        operator_names = [
            "Swap Shifts (Same Day)",
            "Swap All Shifts (Two Days)",
            "Cyclic Swap",
            "Move Pattern",
            "Swap Pattern",
            "Three-Nurse Rotation"
        ]
        for idx, name in enumerate(operator_names):
            if idx in operator_stats:
                stats_op = operator_stats[idx]
                attempts = stats_op['attempts']
                accepted = stats_op['accepted']
                rate = (accepted / attempts * 100) if attempts > 0 else 0.0
                f.write(f"{name:<30} {attempts:>6} attempts, {accepted:>4} accepted ({rate:>5.2f}%)\n")
        
        f.write("="*80 + "\n")


# ============================================================================
# MAIN TESTING LOOP
# ============================================================================

# Store all results for summary
all_results = []

# CSV file for summary
summary_csv_path = RUN_DIR / 'summary.csv'
csv_file = open(summary_csv_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'Instance', 'Lc', 'Run', 'Baseline_Penalty', 'Final_Penalty', 'Improvement', 
    'Improvement_Pct', 'Iterations', 'Time_Sec', 'Accepted_Moves', 'Bound_Updates'
])

for instance_path in INSTANCES:
    # Check if instance exists
    if not Path(instance_path).exists():
        print(f"CAUTION Skipping {instance_path} (file not found)")
        continue
    
    instance_name = Path(instance_path).stem
    
    print("="*80)
    print(f"TESTING: {instance_name}")
    print("="*80)
    
    # Load instance
    try:
        instance = load_instance(instance_path)
        print(f"Loaded: {instance['name']} ({len(instance['nurses'])} nurses, {instance['period']} days)")
    except Exception as e:
        print(f"ERROR loading instance: {e}")
        continue
    
    # Generate baseline
    baseline = greedy_constructor(instance)
    baseline_penalty = evaluate_solution(baseline, instance)
    
    print(f"Baseline penalty: {baseline_penalty}")
    print()
    
    # Test each Lc value
    for lc_value in LC_VALUES:
        algo_name = "HC" if lc_value == 0 else f"SCHC-{lc_value}"
        print(f"  Testing {algo_name}:")
        
        # Run multiple times
        for run in range(1, NUM_RUNS + 1):
            print(f"    Run {run}/{NUM_RUNS}...", end=" ", flush=True)
            
            # Initialize algorithm
            if lc_value == 0:
                algorithm = HillClimbing(
                    instance_data=instance,
                    max_idle_iterations=MAX_IDLE_HC,
                    random_seed=run
                )
            else:
                algorithm = SCHC_all(
                    instance_data=instance,
                    Lc=lc_value,
                    max_idle_iterations=MAX_IDLE_SCHC,
                    random_seed=run
                )
            
            # Optimize
            best_solution, stats = algorithm.optimize(baseline, verbose=False)
            
            # Write to CSV
            csv_writer.writerow([
                instance_name,
                lc_value,
                run,
                baseline_penalty,
                stats['final_penalty'],
                stats['improvement'],
                stats['improvement_percent'],
                stats['iterations'],
                stats['elapsed_time'],
                stats['accepted_moves'],
                stats.get('bound_updates', 0)
            ])
            
            # Save convergence plot
            plot_path = save_convergence_plot(
                stats['penalty_history'],
                instance_name,
                lc_value,
                run
            )
            
            # Save detailed log
            save_detailed_log(
                instance_name,
                lc_value,
                run,
                baseline_penalty,
                stats,
                algorithm.operator_statistics
            )
            
            # Store results
            all_results.append({
                'instance': instance_name,
                'lc': lc_value,
                'run': run,
                'baseline': baseline_penalty,
                'final': stats['final_penalty'],
                'improvement': stats['improvement'],
                'improvement_pct': stats['improvement_percent'],
                'iterations': stats['iterations'],
                'time': stats['elapsed_time']
            })
            
            print(f"Penalty: {baseline_penalty} → {stats['final_penalty']} ({stats['improvement_percent']:.1f}%), Time: {stats['elapsed_time']:.1f}s")
        
        print()
    
    print()

csv_file.close()

# ============================================================================
# SUMMARY STATISTICS BY INSTANCE
# ============================================================================

print("="*80)
print("SUMMARY STATISTICS BY INSTANCE")
print("="*80)
print()

from collections import defaultdict

# Group by instance and Lc
by_instance_lc = defaultdict(lambda: defaultdict(list))
for result in all_results:
    by_instance_lc[result['instance']][result['lc']].append(result)

# Print summary table
print(f"{'Instance':<20} {'Lc':<10} {'Baseline':>10} {'Best':>10} {'Worst':>10} {'Avg':>10} {'StdDev':>10} {'Avg%':>10}")
print("-"*100)

for instance_name in sorted(by_instance_lc.keys()):
    first_row = True
    for lc_value in sorted(by_instance_lc[instance_name].keys()):
        results = by_instance_lc[instance_name][lc_value]
        
        baseline = results[0]['baseline']
        finals = [r['final'] for r in results]
        improvements = [r['improvement_pct'] for r in results]
        
        best = min(finals)
        worst = max(finals)
        avg = sum(finals) / len(finals)
        stddev = (sum((x - avg)**2 for x in finals) / len(finals))**0.5
        avg_pct = sum(improvements) / len(improvements)
        
        lc_label = "HC" if lc_value == 0 else f"SCHC-{lc_value}"
        instance_col = instance_name if first_row else ""
        baseline_col = baseline if first_row else ""
        
        print(f"{instance_col:<20} {lc_label:<10} {baseline_col:>10} {best:>10} {worst:>10} {avg:>10.1f} {stddev:>10.1f} {avg_pct:>9.1f}%")
        first_row = False
    
    print("-"*100)

print("="*80)
print()


# ============================================================================
# AGGREGATE COMPARISON
# ============================================================================

print("="*80)
print("AGGREGATE COMPARISON ACROSS ALL INSTANCES")
print("="*80)
print()

# Group by Lc only (aggregate all instances)
by_lc = defaultdict(list)
for result in all_results:
    by_lc[result['lc']].append(result)

print(f"{'Lc':<10} {'Avg Final':>12} {'Avg %':>10} {'StdDev':>10} {'Avg Iter':>10} {'Avg Time':>10}")
print("-"*70)

for lc_value in sorted(by_lc.keys()):
    results = by_lc[lc_value]
    
    finals = [r['final'] for r in results]
    improvements = [r['improvement_pct'] for r in results]
    iterations = [r['iterations'] for r in results]
    times = [r['time'] for r in results]
    
    avg_final = sum(finals) / len(finals)
    avg_pct = sum(improvements) / len(improvements)
    stddev = (sum((x - avg_final)**2 for x in finals) / len(finals))**0.5
    avg_iter = sum(iterations) / len(iterations)
    avg_time = sum(times) / len(times)
    
    lc_label = "HC" if lc_value == 0 else f"SCHC-{lc_value}"
    print(f"{lc_label:<10} {avg_final:>12.1f} {avg_pct:>9.1f}% {stddev:>10.1f} {avg_iter:>10.0f} {avg_time:>9.1f}s")

print("="*80)
print()


# ============================================================================
# HC vs SCHC COMPARISON
# ============================================================================

print("="*80)
print("HC vs SCHC DETAILED COMPARISON")
print("="*80)
print()

hc_results = by_lc[0]
hc_finals = [r['final'] for r in hc_results]
hc_avg = sum(hc_finals) / len(hc_finals)
hc_stddev = (sum((x - hc_avg)**2 for x in hc_finals) / len(hc_finals))**0.5

for lc_value in sorted(by_lc.keys()):
    if lc_value == 0:
        continue
    
    schc_results = by_lc[lc_value]
    schc_finals = [r['final'] for r in schc_results]
    schc_avg = sum(schc_finals) / len(schc_finals)
    schc_stddev = (sum((x - schc_avg)**2 for x in schc_finals) / len(schc_finals))**0.5
    
    avg_diff = hc_avg - schc_avg
    stddev_change = hc_stddev - schc_stddev
    
    print(f"HC vs SCHC-{lc_value}:")
    print(f"  Average penalty:    {hc_avg:.1f} vs {schc_avg:.1f} (Δ = {avg_diff:+.1f})")
    print(f"  Standard deviation: {hc_stddev:.1f} vs {schc_stddev:.1f} (Δ = {stddev_change:+.1f})")
    
    if avg_diff > 0:
        print(f"  SCHC better by {avg_diff:.1f} penalties ({abs(avg_diff)/hc_avg*100:.1f}%)")
    else:
        print(f"  HC better by {abs(avg_diff):.1f} penalties")
    
    # Win/loss analysis
    wins = sum(1 for hc_r, schc_r in zip(hc_results, schc_results) if schc_r['final'] < hc_r['final'])
    losses = sum(1 for hc_r, schc_r in zip(hc_results, schc_results) if schc_r['final'] > hc_r['final'])
    ties = len(hc_results) - wins - losses
    
    print(f"  Win/Loss: {wins}W - {losses}L - {ties}T ({wins/len(hc_results)*100:.0f}% win rate)")
    print()

print("="*80)
print()
print(f"All results saved to: {RUN_DIR}")
print(f"Summary CSV: {summary_csv_path}")
print(f"Detailed logs: {RUN_DIR}/*_detailed.txt")
if HAS_MATPLOTLIB:
    print(f"Convergence plots: {RUN_DIR}/*.png")
print()