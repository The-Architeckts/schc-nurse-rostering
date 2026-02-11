'''
Comprehensive testing for Hill Climbing algorithm.
Tests both standard HC and steepest descent variant.
'''

import sys
import matplotlib.pyplot as plt
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.append(str(src_path))

# Now we can import from src
from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.hill_climbing import HillClimbing, SteepestDescentHC
from constraints import (
    evaluate_solution,
    _check_counter_constraints,
    _check_series_constraints,
    _check_pattern_constraints,
    _check_complete_weekends,
    _check_identical_weekends,
    _check_shift_off_requests,
    _check_time_off_requests
)
from models import ShiftType

# ============================================================================
# SCHEDULE VISUALIZATION HELPER
# ============================================================================

def print_schedule(solution, instance_data, title="SCHEDULE"):
    """
    Print a formatted schedule showing all nurses and all days.
    """
    print("\n" + "="*80)
    print(title)
    print("="*80)
    
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    # Print header with day numbers
    print(f"{'Nurse':<8}", end="")
    for day in range(n_days):
        print(f"{day%10}", end="")
    print()
    
    print("-"*80)
    
    # Print each nurse's schedule
    for nurse_id in range(n_nurses):
        nurse = instance_data['nurses'][nurse_id]
        contract_id = nurse.contract_id
        
        print(f"N{nurse_id} (C{contract_id}): ", end="")
        
        for day in range(n_days):
            shift = solution.schedule[nurse_id][day]
            shift_str = ShiftType.to_string(shift)
            print(shift_str, end="")
        
        print()  # New line after each nurse
    
    print("="*80)
    
    # Print legend
    print("\nLegend: E=Early, L=Late, D=Day, N=Night, -=Off")
    print(f"        (C0-C3 = Contract types)")
    print()


# ============================================================================
# LOAD INSTANCE AND GENERATE BASELINE
# ============================================================================

# Load instance
print("Loading instance...")
instance = load_instance('data/inrc1/INRC1_sprint01.json')

# Generate baseline
print("Generating baseline solution...")
baseline = greedy_constructor(instance)
baseline_penalty = evaluate_solution(baseline, instance)

print(f"Baseline penalty: {baseline_penalty}")
print()

# Print original schedule
print_schedule(baseline, instance, "ORIGINAL BASELINE SCHEDULE (Before Optimization)")

# ============================================================================
# TEST 1: Standard Hill Climbing
# ============================================================================

print("\n" + "="*80)
print("TEST 1: STANDARD HILL CLIMBING (Random Operator Selection)")
print("="*80 + "\n")

hc = HillClimbing(
    instance_data=instance,
    max_idle_iterations=1000,
    random_seed=42  # For reproducibility
)

best_solution, stats = hc.optimize(baseline, verbose=True)

# Print operator statistics
hc.print_operator_statistics()

# PRINT OPTIMIZED SCHEDULE
print_schedule(best_solution, instance, 
               f"OPTIMIZED SCHEDULE - STANDARD HC (Penalty: {stats['final_penalty']})")

# Detailed constraint breakdown
print("\n" + "="*80)
print("CONSTRAINT BREAKDOWN COMPARISON")
print("="*80)

from constraints import (
    _check_counter_constraints,
    _check_series_constraints,
    _check_pattern_constraints,
    _check_complete_weekends,
    _check_identical_weekends,
    _check_shift_off_requests,
    _check_time_off_requests
)

print(f"\n{'Constraint Type':<25} {'Baseline':>10} {'HC Final':>10} {'Change':>10}")
print("-"*80)

# Calculate penalties for baseline
baseline_counter = 0
baseline_series = 0
baseline_pattern = 0
baseline_complete = 0
baseline_identical = 0
baseline_shift_off = 0
baseline_time_off = 0

for nurse_id, nurse in enumerate(instance['nurses']):
    contract = instance['contracts'][nurse.contract_id]
    schedule = baseline.schedule[nurse_id]
    
    baseline_counter += _check_counter_constraints(contract, schedule)
    baseline_series += _check_series_constraints(contract, schedule)
    baseline_pattern += _check_pattern_constraints(contract, schedule)
    baseline_complete += _check_complete_weekends(nurse, schedule, instance)
    baseline_identical += _check_identical_weekends(nurse, schedule, instance)
    baseline_shift_off += _check_shift_off_requests(nurse, schedule)
    baseline_time_off += _check_time_off_requests(nurse, schedule)

# Calculate penalties for HC solution
hc_counter = 0
hc_series = 0
hc_pattern = 0
hc_complete = 0
hc_identical = 0
hc_shift_off = 0
hc_time_off = 0

for nurse_id, nurse in enumerate(instance['nurses']):
    contract = instance['contracts'][nurse.contract_id]
    schedule = best_solution.schedule[nurse_id]
    
    hc_counter += _check_counter_constraints(contract, schedule)
    hc_series += _check_series_constraints(contract, schedule)
    hc_pattern += _check_pattern_constraints(contract, schedule)
    hc_complete += _check_complete_weekends(nurse, schedule, instance)
    hc_identical += _check_identical_weekends(nurse, schedule, instance)
    hc_shift_off += _check_shift_off_requests(nurse, schedule)
    hc_time_off += _check_time_off_requests(nurse, schedule)

# Print comparison
constraints = [
    ("Counter", baseline_counter, hc_counter),
    ("Series", baseline_series, hc_series),
    ("Pattern", baseline_pattern, hc_pattern),
    ("Complete Weekend", baseline_complete, hc_complete),
    ("Identical Weekend", baseline_identical, hc_identical),
    ("Shift-Off Requests", baseline_shift_off, hc_shift_off),
    ("Time-Off Requests", baseline_time_off, hc_time_off),
]

for name, base_val, hc_val in constraints:
    change = hc_val - base_val
    print(f"{name:<25} {base_val:>10} {hc_val:>10} {change:>+10}")

print("-"*80)
print(f"{'TOTAL':<25} {baseline_penalty:>10} {stats['final_penalty']:>10} {stats['final_penalty'] - baseline_penalty:>+10}")
print("="*80)


# ============================================================================
# TEST 2: Steepest Descent Hill Climbing
# ============================================================================

print("\n" + "="*80)
print("TEST 2: STEEPEST DESCENT HILL CLIMBING (Best Operator Selection)")
print("="*80 + "\n")

sdhc = SteepestDescentHC(
    instance_data=instance,
    max_idle_iterations=100,  # Fewer iterations (each iteration is expensive)
    random_seed=42
)

best_solution_sd, stats_sd = sdhc.optimize(baseline, verbose=True)

sdhc.print_operator_statistics()

# PRINT OPTIMIZED SCHEDULE
print_schedule(best_solution_sd, instance, 
               f"OPTIMIZED SCHEDULE - STEEPEST DESCENT HC (Penalty: {stats_sd['final_penalty']})")

# ============================================================================
# TEST 3: Multiple Runs Comparison
# ============================================================================

print("\n" + "="*80)
print("TEST 3: MULTIPLE RUNS (Testing Variability)")
print("="*80 + "\n")

print("Running standard HC 10 times with different random seeds...")
print()

results = []
for run in range(10):
    hc_run = HillClimbing(
        instance_data=instance,
        max_idle_iterations=1000,
        random_seed=run
    )
    
    _, stats_run = hc_run.optimize(baseline, verbose=False)
    results.append(stats_run['final_penalty'])
    
    print(f"Run {run+1:2d}: Initial={stats_run['initial_penalty']:3d} → "
          f"Final={stats_run['final_penalty']:3d} "
          f"(Δ={stats_run['improvement']:+3d}, {stats_run['improvement_percent']:5.1f}%)")

print()
print(f"Best result:     {min(results)}")
print(f"Worst result:    {max(results)}")
print(f"Average result:  {sum(results)/len(results):.1f}")
print(f"Std deviation:   {(sum((x - sum(results)/len(results))**2 for x in results) / len(results))**0.5:.1f}")


# ============================================================================
# TEST 4: Convergence Analysis
# ============================================================================

print("\n" + "="*80)
print("TEST 4: CONVERGENCE ANALYSIS")
print("="*80 + "\n")

# Plot convergence curve
try:
    plt.figure(figsize=(12, 6))
    
    # Plot HC convergence
    plt.subplot(1, 2, 1)
    iterations = list(range(0, len(stats['penalty_history']) * 10, 10))
    plt.plot(iterations, stats['penalty_history'], 'b-', linewidth=2)
    plt.xlabel('Iteration')
    plt.ylabel('Penalty')
    plt.title('Standard Hill Climbing Convergence')
    plt.grid(True, alpha=0.3)
    
    # Plot SD HC convergence
    plt.subplot(1, 2, 2)
    iterations_sd = list(range(0, len(stats_sd['penalty_history']) * 10, 10))
    plt.plot(iterations_sd, stats_sd['penalty_history'], 'r-', linewidth=2)
    plt.xlabel('Iteration')
    plt.ylabel('Penalty')
    plt.title('Steepest Descent HC Convergence')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hc_convergence.png', dpi=150)
    print("✅ Convergence plot saved as 'hc_convergence.png'")
    print()
except Exception as e:
    print(f"⚠️ Could not generate plot: {e}")
    print("(Install matplotlib if you want convergence plots)")
    print()


# ============================================================================
# SUMMARY
# ============================================================================

print("="*80)
print("SUMMARY")
print("="*80)
print()
print(f"Baseline penalty:           {baseline_penalty}")
print(f"HC final penalty:           {stats['final_penalty']}")
print(f"SD HC final penalty:        {stats_sd['final_penalty']}")
print()
print(f"HC improvement:             {stats['improvement']} ({stats['improvement_percent']:.1f}%)")
print(f"SD HC improvement:          {stats_sd['improvement']} ({stats_sd['improvement_percent']:.1f}%)")
print()
print(f"HC iterations:              {stats['iterations']}")
print(f"SD HC iterations:           {stats_sd['iterations']}")
print()
print(f"HC time:                    {stats['elapsed_time']:.2f}s")
print(f"SD HC time:                 {stats_sd['elapsed_time']:.2f}s")
print()
print("="*80)