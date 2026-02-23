'''
Comprehensive testing for SCHC algorithm.
Compares HC (Lc=0) vs SCHC (Lc>0) with various counter limits.
'''

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.hill_climbing import HillClimbing
from algorithms.schc import SCHC_all
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

# Test instance
INSTANCE_PATH = 'data/inrc1/INRC1_sprint01.json'

# Lc values to test
LC_VALUES = [0, 50, 100, 200]  # 0 = standard HC

# Number of runs per Lc
NUM_RUNS = 10

# Max idle iterations (increase for SCHC to allow exploration)
MAX_IDLE_HC = 1000
MAX_IDLE_SCHC = 5000

print("="*80)
print("SCHC vs HC COMPARISON")
print("="*80)
print(f"Instance: {INSTANCE_PATH}")
print(f"Testing Lc values: {LC_VALUES}")
print(f"Runs per Lc: {NUM_RUNS}")
print()


# ============================================================================
# LOAD INSTANCE AND BASELINE
# ============================================================================

instance = load_instance(INSTANCE_PATH)
baseline = greedy_constructor(instance)
baseline_penalty = evaluate_solution(baseline, instance)

print(f"Instance: {instance['name']} ({len(instance['nurses'])} nurses, {instance['period']} days)")
print(f"Baseline penalty: {baseline_penalty}")
print()


# ============================================================================
# TEST EACH Lc VALUE
# ============================================================================

all_results = {}

for Lc in LC_VALUES:
    print("="*80)
    if Lc == 0:
        print(f"TESTING: Standard Hill Climbing (Lc={Lc})")
    else:
        print(f"TESTING: SCHC-all (Lc={Lc})")
    print("="*80)
    print()
    
    results = []
    
    for run in range(1, NUM_RUNS + 1):
        print(f"Run {run}/{NUM_RUNS}...", end=" ", flush=True)
        
        if Lc == 0:
            # Standard Hill Climbing
            algorithm = HillClimbing(
                instance_data=instance,
                max_idle_iterations=MAX_IDLE_HC,
                random_seed=run
            )
        else:
            # SCHC-all
            algorithm = SCHC_all(
                instance_data=instance,
                Lc=Lc,
                max_idle_iterations=MAX_IDLE_SCHC,
                random_seed=run
            )
        
        best_solution, stats = algorithm.optimize(baseline, verbose=False)
        
        results.append({
            'run': run,
            'Lc': Lc,
            'final_penalty': stats['final_penalty'],
            'improvement': stats['improvement'],
            'improvement_pct': stats['improvement_percent'],
            'iterations': stats['iterations'],
            'time': stats['elapsed_time'],
            'penalty_history': stats['penalty_history'],
            'bound_updates': stats.get('bound_updates', 0)  # Only SCHC has this
        })
        
        print(f"Penalty: {baseline_penalty} → {stats['final_penalty']} "
              f"({stats['improvement_percent']:.1f}%), "
              f"Iterations: {stats['iterations']}, "
              f"Time: {stats['elapsed_time']:.1f}s")
    
    all_results[Lc] = results
    print()


# ============================================================================
# COMPARISON STATISTICS
# ============================================================================

print("="*80)
print("COMPARISON SUMMARY")
print("="*80)
print()

print(f"{'Lc':<10} {'Best':>10} {'Worst':>10} {'Average':>10} {'StdDev':>10} "
      f"{'Avg%':>10} {'AvgIter':>10} {'AvgTime':>10}")
print("-"*90)

for Lc in LC_VALUES:
    results = all_results[Lc]
    
    finals = [r['final_penalty'] for r in results]
    improvements = [r['improvement_pct'] for r in results]
    iterations = [r['iterations'] for r in results]
    times = [r['time'] for r in results]
    
    best = min(finals)
    worst = max(finals)
    avg = sum(finals) / len(finals)
    stddev = (sum((x - avg)**2 for x in finals) / len(finals))**0.5
    avg_pct = sum(improvements) / len(improvements)
    avg_iter = sum(iterations) / len(iterations)
    avg_time = sum(times) / len(times)
    
    lc_label = "HC" if Lc == 0 else f"SCHC-{Lc}"
    print(f"{lc_label:<10} {best:>10} {worst:>10} {avg:>10.1f} {stddev:>10.1f} "
          f"{avg_pct:>9.1f}% {avg_iter:>10.0f} {avg_time:>9.1f}s")

print("="*80)
print()


# ============================================================================
# DETAILED COMPARISON
# ============================================================================

print("="*80)
print("HC vs SCHC ANALYSIS")
print("="*80)
print()

# Compare HC vs each SCHC variant
hc_results = all_results[0]
hc_avg = sum(r['final_penalty'] for r in hc_results) / len(hc_results)
hc_stddev = (sum((r['final_penalty'] - hc_avg)**2 for r in hc_results) / len(hc_results))**0.5

for Lc in [50, 100, 200]:
    schc_results = all_results[Lc]
    schc_avg = sum(r['final_penalty'] for r in schc_results) / len(schc_results)
    schc_stddev = (sum((r['final_penalty'] - schc_avg)**2 for r in schc_results) / len(schc_results))**0.5
    
    avg_diff = hc_avg - schc_avg
    stddev_change = hc_stddev - schc_stddev
    
    print(f"HC (Lc=0) vs SCHC (Lc={Lc}):")
    print(f"  Average penalty:    {hc_avg:.1f} vs {schc_avg:.1f} (Δ = {avg_diff:+.1f})")
    print(f"  Standard deviation: {hc_stddev:.1f} vs {schc_stddev:.1f} (Δ = {stddev_change:+.1f})")
    
    if avg_diff > 0:
        print(f"  ✅ SCHC better by {avg_diff:.1f} penalties ({abs(avg_diff)/hc_avg*100:.1f}%)")
    elif avg_diff < 0:
        print(f"  ❌ HC better by {abs(avg_diff):.1f} penalties ({abs(avg_diff)/hc_avg*100:.1f}%)")
    else:
        print(f"  ➖ Same average performance")
    
    # Check if SCHC improves worst-case
    hc_worst = max(r['final_penalty'] for r in hc_results)
    schc_worst = max(r['final_penalty'] for r in schc_results)
    
    if schc_worst < hc_worst:
        print(f"  ✅ SCHC improves worst-case: {hc_worst} → {schc_worst} ({hc_worst-schc_worst} better)")
    
    print()


# ============================================================================
# CONVERGENCE PLOTS
# ============================================================================

if HAS_MATPLOTLIB:
    print("Generating convergence comparison plot...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Hill Climbing vs SCHC Convergence Comparison', fontsize=16, fontweight='bold')
    
    colors = ['blue', 'green', 'orange', 'red']
    
    for idx, Lc in enumerate(LC_VALUES):
        ax = axes[idx // 2, idx % 2]
        
        # Plot all runs for this Lc
        results = all_results[Lc]
        for r in results:
            history = r['penalty_history']
            iterations = list(range(0, len(history) * 10, 10))
            ax.plot(iterations, history, alpha=0.3, color=colors[idx], linewidth=1)
        
        # Plot average
        max_len = max(len(r['penalty_history']) for r in results)
        avg_history = []
        for i in range(max_len):
            values = [r['penalty_history'][i] for r in results if i < len(r['penalty_history'])]
            avg_history.append(sum(values) / len(values))
        
        iterations = list(range(0, len(avg_history) * 10, 10))
        ax.plot(iterations, avg_history, color=colors[idx], linewidth=3, label='Average')
        
        title = f"Standard HC (Lc={Lc})" if Lc == 0 else f"SCHC-all (Lc={Lc})"
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('Iteration', fontsize=10)
        ax.set_ylabel('Penalty', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    plt.savefig('schc_comparison.png', dpi=150, bbox_inches='tight')
    print("✅ Convergence plot saved as 'schc_comparison.png'")
    print()


# ============================================================================
# WIN/LOSS ANALYSIS
# ============================================================================

print("="*80)
print("HEAD-TO-HEAD COMPARISON (Run by Run)")
print("="*80)
print()

hc_results = all_results[0]

for Lc in [50, 100, 200]:
    schc_results = all_results[Lc]
    
    wins = 0
    losses = 0
    ties = 0
    
    for hc_r, schc_r in zip(hc_results, schc_results):
        if schc_r['final_penalty'] < hc_r['final_penalty']:
            wins += 1
        elif schc_r['final_penalty'] > hc_r['final_penalty']:
            losses += 1
        else:
            ties += 1
    
    print(f"HC (Lc=0) vs SCHC (Lc={Lc}): {wins} wins, {losses} losses, {ties} ties")
    
    if wins > losses:
        print(f"  ✅ SCHC wins {wins}/{NUM_RUNS} runs ({wins/NUM_RUNS*100:.0f}%)")
    elif losses > wins:
        print(f"  ❌ HC wins {losses}/{NUM_RUNS} runs ({losses/NUM_RUNS*100:.0f}%)")
    else:
        print(f"  ➖ Tied performance")
    
    print()


print("="*80)
print("TESTING COMPLETE")
print("="*80)