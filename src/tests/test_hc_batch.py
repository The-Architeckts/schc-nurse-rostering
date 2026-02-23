"""
Batch testing of Hill Climbing on multiple INRC-I instances.
Automatically logs all results with timestamps and unique file names.
"""

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
from algorithms.hill_climbing import HillClimbing, SteepestDescentHC
from constraints import evaluate_solution
from models import ShiftType

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for batch processing
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available, skipping convergence plots")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Instance sets to test
INSTANCE_SETS = {
    'standard': [f'data/inrc1/INRC1_sprint{i:02d}.json' for i in range(1, 11)],
    'hidden': [f'data/inrc1/INRC1_sprint_hidden{i:02d}.json' for i in range(1, 11)],
    'late': [f'data/inrc1/INRC1_sprint_late{i:02d}.json' for i in range(1, 11)],
}

# Select which set to test (change this as needed)
TEST_SET = 'standard'  # Options: 'standard', 'hidden', 'late', or 'all'

if TEST_SET == 'all':
    INSTANCES = INSTANCE_SETS['standard'] + INSTANCE_SETS['hidden'] + INSTANCE_SETS['late']
else:
    INSTANCES = INSTANCE_SETS[TEST_SET]

print(f"Testing instance set: {TEST_SET.upper()}")
print(f"Number of instances: {len(INSTANCES)}")
print()

# Number of runs per instance
NUM_RUNS = 10

# HC configuration
MAX_IDLE_ITERATIONS = 1000

# Create output directory
OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

# Create timestamped subdirectory for this test run
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR = OUTPUT_DIR / f'hc_{TEST_SET}_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

print(f"Output directory: {RUN_DIR}")
print(f"Testing {len(INSTANCES)} instances with {NUM_RUNS} runs each")
print(f"Total runs: {len(INSTANCES) * NUM_RUNS}")
print()


# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

def save_convergence_plot(penalty_history, instance_name, run_number, variant="standard"):
    """Save convergence plot with unique filename."""
    if not HAS_MATPLOTLIB:
        return None
    
    plt.figure(figsize=(10, 6))
    iterations = list(range(0, len(penalty_history) * 10, 10))
    plt.plot(iterations, penalty_history, 'b-', linewidth=2)
    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Penalty', fontsize=12)
    plt.title(f'{instance_name} - {variant.upper()} HC - Run {run_number}', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Save with unique name
    filename = f'{instance_name}_{variant}_run{run_number:02d}.png'
    filepath = RUN_DIR / filename
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    return str(filepath)


def save_detailed_log(instance_name, run_number, baseline_penalty, stats, 
                      operator_stats, constraint_breakdown):
    """Save detailed log file for this run."""
    filename = f'{instance_name}_run{run_number:02d}_detailed.txt'
    filepath = RUN_DIR / filename
    
    with open(filepath, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"HILL CLIMBING DETAILED RESULTS\n")
        f.write("="*80 + "\n")
        f.write(f"Instance: {instance_name}\n")
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
        f.write("\n")
        
        f.write("CONSTRAINT BREAKDOWN:\n")
        f.write("-"*80 + "\n")
        f.write(f"{'Constraint':<25} {'Baseline':>10} {'Final':>10} {'Change':>10}\n")
        f.write("-"*80 + "\n")
        for name, baseline_val, final_val in constraint_breakdown:
            change = final_val - baseline_val
            f.write(f"{name:<25} {baseline_val:>10} {final_val:>10} {change:>+10}\n")
        f.write("-"*80 + "\n")
        f.write(f"{'TOTAL':<25} {baseline_penalty:>10} {stats['final_penalty']:>10} {stats['final_penalty']-baseline_penalty:>+10}\n")
        f.write("="*80 + "\n")


# ============================================================================
# CONSTRAINT BREAKDOWN CALCULATOR
# ============================================================================

def calculate_constraint_breakdown(solution, instance_data):
    """Calculate penalty breakdown by constraint type."""
    from constraints import (
        _check_counter_constraints,
        _check_series_constraints,
        _check_pattern_constraints,
        _check_complete_weekends,
        _check_identical_weekends,
        _check_shift_off_requests,
        _check_time_off_requests
    )
    
    counter = series = pattern = complete = identical = shift_off = time_off = 0
    
    for nurse_id, nurse in enumerate(instance_data['nurses']):
        contract = instance_data['contracts'][nurse.contract_id]
        schedule = solution.schedule[nurse_id]
        
        counter += _check_counter_constraints(contract, schedule)
        series += _check_series_constraints(contract, schedule)
        pattern += _check_pattern_constraints(contract, schedule)
        complete += _check_complete_weekends(nurse, schedule, instance_data)
        identical += _check_identical_weekends(nurse, schedule, instance_data)
        shift_off += _check_shift_off_requests(nurse, schedule)
        time_off += _check_time_off_requests(nurse, schedule)
    
    return [
        ("Counter", counter),
        ("Series", series),
        ("Pattern", pattern),
        ("Complete Weekend", complete),
        ("Identical Weekend", identical),
        ("Shift-Off Requests", shift_off),
        ("Time-Off Requests", time_off),
    ]


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
    'Instance', 'Run', 'Baseline_Penalty', 'Final_Penalty', 'Improvement', 
    'Improvement_Pct', 'Iterations', 'Time_Sec', 'Accepted_Moves',
    'Counter_Before', 'Counter_After', 'Series_Before', 'Series_After',
    'Pattern_Before', 'Pattern_After', 'CompleteWknd_Before', 'CompleteWknd_After',
    'TimeOff_Before', 'TimeOff_After'
])

for instance_path in INSTANCES:
    # Check if instance exists
    if not Path(instance_path).exists():
        print(f"⚠️  Skipping {instance_path} (file not found)")
        continue
    
    instance_name = Path(instance_path).stem  # e.g., "INRC1_sprint01"
    
    print("="*80)
    print(f"TESTING: {instance_name}")
    print("="*80)
    
    # Load instance
    try:
        instance = load_instance(instance_path)
        print(f"Loaded: {instance['name']} ({len(instance['nurses'])} nurses, {instance['period']} days)")
    except Exception as e:
        print(f"❌ Error loading instance: {e}")
        continue
    
    # Generate baseline
    baseline = greedy_constructor(instance)
    baseline_penalty = evaluate_solution(baseline, instance)
    baseline_breakdown = calculate_constraint_breakdown(baseline, instance)
    
    print(f"Baseline penalty: {baseline_penalty}")
    print()
    
    # Run HC multiple times
    for run in range(1, NUM_RUNS + 1):
        print(f"  Run {run}/{NUM_RUNS}...", end=" ", flush=True)
        
        # Initialize HC
        hc = HillClimbing(
            instance_data=instance,
            max_idle_iterations=MAX_IDLE_ITERATIONS,
            random_seed=run  # Different seed per run
        )
        
        # Optimize
        best_solution, stats = hc.optimize(baseline, verbose=False)
        
        # Calculate constraint breakdown
        final_breakdown = calculate_constraint_breakdown(best_solution, instance)
        
        # Prepare constraint data for CSV
        constraint_dict = {}
        for (name_b, val_b), (name_f, val_f) in zip(baseline_breakdown, final_breakdown):
            constraint_dict[f'{name_b}_Before'] = val_b
            constraint_dict[f'{name_f}_After'] = val_f
        
        # Write to CSV
        csv_writer.writerow([
            instance_name,
            run,
            baseline_penalty,
            stats['final_penalty'],
            stats['improvement'],
            stats['improvement_percent'],
            stats['iterations'],
            stats['elapsed_time'],
            stats['accepted_moves'],
            constraint_dict.get('Counter_Before', 0),
            constraint_dict.get('Counter_After', 0),
            constraint_dict.get('Series_Before', 0),
            constraint_dict.get('Series_After', 0),
            constraint_dict.get('Pattern_Before', 0),
            constraint_dict.get('Pattern_After', 0),
            constraint_dict.get('Complete Weekend_Before', 0),
            constraint_dict.get('Complete Weekend_After', 0),
            constraint_dict.get('Time-Off Requests_Before', 0),
            constraint_dict.get('Time-Off Requests_After', 0),
        ])
        
        # Save convergence plot
        plot_path = save_convergence_plot(
            stats['penalty_history'],
            instance_name,
            run,
            variant="standard"
        )
        
        # Save detailed log
        save_detailed_log(
            instance_name,
            run,
            baseline_penalty,
            stats,
            hc.operator_statistics,
            [(name_b, val_b, val_f) for (name_b, val_b), (name_f, val_f) 
             in zip(baseline_breakdown, final_breakdown)]
        )
        
        # Store results
        all_results.append({
            'instance': instance_name,
            'run': run,
            'baseline': baseline_penalty,
            'final': stats['final_penalty'],
            'improvement': stats['improvement'],
            'improvement_pct': stats['improvement_percent'],
        })
        
        print(f"Penalty: {baseline_penalty} → {stats['final_penalty']} ({stats['improvement_percent']:.1f}%)")
    
    print()

csv_file.close()

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("="*80)
print("SUMMARY STATISTICS")
print("="*80)
print()

# Group by instance
from collections import defaultdict
by_instance = defaultdict(list)
for result in all_results:
    by_instance[result['instance']].append(result)

# Print summary table
print(f"{'Instance':<20} {'Baseline':>10} {'Best':>10} {'Worst':>10} {'Avg':>10} {'StdDev':>10} {'Avg%':>10}")
print("-"*90)

for instance_name in sorted(by_instance.keys()):
    results = by_instance[instance_name]
    
    baseline = results[0]['baseline']
    finals = [r['final'] for r in results]
    improvements = [r['improvement_pct'] for r in results]
    
    best = min(finals)
    worst = max(finals)
    avg = sum(finals) / len(finals)
    stddev = (sum((x - avg)**2 for x in finals) / len(finals))**0.5
    avg_pct = sum(improvements) / len(improvements)
    
    print(f"{instance_name:<20} {baseline:>10} {best:>10} {worst:>10} {avg:>10.1f} {stddev:>10.1f} {avg_pct:>9.1f}%")

print("="*80)
print()
print(f"✅ All results saved to: {RUN_DIR}")
print(f"✅ Summary CSV: {summary_csv_path}")
print(f"✅ Detailed logs: {RUN_DIR}/*_detailed.txt")
if HAS_MATPLOTLIB:
    print(f"✅ Convergence plots: {RUN_DIR}/*.png")
print()