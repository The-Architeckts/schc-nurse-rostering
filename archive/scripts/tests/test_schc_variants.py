'''
Comprehensive comparison of SCHC variants (all, acp, imp).
Tests on representative instances to identify best-performing variant.
'''

import sys
from pathlib import Path
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

# Test instances: development baseline + hardest + highest variance
INSTANCES = [
    'data/inrc1/INRC1_sprint01.json',  # Development baseline
    'data/inrc1/INRC1_sprint04.json',  # Hardest (worst HC performance)
    'data/inrc1/INRC1_sprint10.json',  # Highest variance
]

# Variants to compare
VARIANTS = ['all', 'acp', 'imp']

# Lc value (use optimal from previous testing)
LC_VALUE = 100

# Runs per configuration
NUM_RUNS = 10

# Output directory
OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR = OUTPUT_DIR / f'schc_variants_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

print("="*80)
print("SCHC VARIANT COMPARISON")
print("="*80)
print(f"Testing {len(INSTANCES)} instances")
print(f"Variants: {VARIANTS}")
print(f"Lc value: {LC_VALUE}")
print(f"Runs per configuration: {NUM_RUNS}")
print(f"Output directory: {RUN_DIR}")
print()


# ============================================================================
# TESTING LOOP
# ============================================================================

all_results = []

# CSV file
summary_csv_path = RUN_DIR / 'summary.csv'
csv_file = open(summary_csv_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'Instance', 'Variant', 'Run', 'Baseline', 'Final', 
    'Improvement', 'Improvement_Pct', 'Iterations', 'Bound_Updates', 'Time'
])

for instance_path in INSTANCES:
    if not Path(instance_path).exists():
        print(f"CAUTION Skipping {instance_path}")
        continue
    
    instance_name = Path(instance_path).stem
    
    print("="*80)
    print(f"TESTING: {instance_name}")
    print("="*80)
    
    # Load instance
    instance = load_instance(instance_path)
    print(f"Loaded: {instance['name']} ({len(instance['nurses'])} nurses, {instance['period']} days)")
    
    # Generate baseline
    baseline = greedy_constructor(instance)
    baseline_penalty = evaluate_solution(baseline, instance)
    print(f"Baseline penalty: {baseline_penalty}")
    print()
    
    # Test HC baseline first
    print("  Testing HC (baseline):")
    for run in range(1, NUM_RUNS + 1):
        print(f"    Run {run}/{NUM_RUNS}...", end=" ", flush=True)
        
        hc = HillClimbing(
            instance_data=instance,
            max_idle_iterations=1000,
            random_seed=run
        )
        
        best_solution, stats = hc.optimize(baseline, verbose=False)
        
        csv_writer.writerow([
            instance_name, 'HC', run, baseline_penalty, stats['final_penalty'],
            stats['improvement'], stats['improvement_percent'], 
            stats['iterations'], 0, stats['elapsed_time']
        ])
        
        all_results.append({
            'instance': instance_name,
            'variant': 'HC',
            'run': run,
            'baseline': baseline_penalty,
            'final': stats['final_penalty'],
            'improvement_pct': stats['improvement_percent'],
            'iterations': stats['iterations'],
            'bound_updates': 0,
            'time': stats['elapsed_time']
        })
        
        print(f"{baseline_penalty} → {stats['final_penalty']} ({stats['improvement_percent']:.1f}%)")
    
    print()
    
    # Test each SCHC variant
    for variant in VARIANTS:
        print(f"  Testing SCHC-{variant}:")
        
        for run in range(1, NUM_RUNS + 1):
            print(f"    Run {run}/{NUM_RUNS}...", end=" ", flush=True)
            
            schc = SCHC(
                instance_data=instance,
                Lc=LC_VALUE,
                variant=variant,
                max_idle_iterations=5000,
                random_seed=run
            )
            
            best_solution, stats = schc.optimize(baseline, verbose=False)
            
            csv_writer.writerow([
                instance_name, f'SCHC-{variant}', run, baseline_penalty, 
                stats['final_penalty'], stats['improvement'], 
                stats['improvement_percent'], stats['iterations'], 
                stats['bound_updates'], stats['elapsed_time']
            ])
            
            all_results.append({
                'instance': instance_name,
                'variant': f'SCHC-{variant}',
                'run': run,
                'baseline': baseline_penalty,
                'final': stats['final_penalty'],
                'improvement_pct': stats['improvement_percent'],
                'iterations': stats['iterations'],
                'bound_updates': stats['bound_updates'],
                'time': stats['elapsed_time']
            })
            
            print(f"{baseline_penalty} → {stats['final_penalty']} ({stats['improvement_percent']:.1f}%), "
                  f"Updates: {stats['bound_updates']}, Time: {stats['elapsed_time']:.1f}s")
        
        print()
    
    print()

csv_file.close()


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("="*80)
print("SUMMARY STATISTICS BY INSTANCE")
print("="*80)
print()

# Group by instance and variant
by_instance_variant = defaultdict(lambda: defaultdict(list))
for result in all_results:
    by_instance_variant[result['instance']][result['variant']].append(result)

print(f"{'Instance':<20} {'Variant':<15} {'Best':>8} {'Worst':>8} {'Avg':>8} {'StdDev':>8} {'Avg%':>8} {'AvgUpd':>8}")
print("-"*95)

for instance_name in sorted(by_instance_variant.keys()):
    first_row = True
    for variant in ['HC', 'SCHC-all', 'SCHC-acp', 'SCHC-imp']:
        if variant not in by_instance_variant[instance_name]:
            continue
        
        results = by_instance_variant[instance_name][variant]
        
        finals = [r['final'] for r in results]
        improvements = [r['improvement_pct'] for r in results]
        updates = [r['bound_updates'] for r in results]
        
        best = min(finals)
        worst = max(finals)
        avg = sum(finals) / len(finals)
        stddev = (sum((x - avg)**2 for x in finals) / len(finals))**0.5
        avg_pct = sum(improvements) / len(improvements)
        avg_upd = sum(updates) / len(updates)
        
        instance_col = instance_name if first_row else ""
        print(f"{instance_col:<20} {variant:<15} {best:>8} {worst:>8} {avg:>8.1f} {stddev:>8.1f} {avg_pct:>7.1f}% {avg_upd:>8.0f}")
        first_row = False
    
    print("-"*95)

print("="*80)
print()


# ============================================================================
# AGGREGATE COMPARISON
# ============================================================================

print("="*80)
print("AGGREGATE COMPARISON (ALL INSTANCES)")
print("="*80)
print()

by_variant = defaultdict(list)
for result in all_results:
    by_variant[result['variant']].append(result)

print(f"{'Variant':<15} {'Avg Final':>12} {'Avg%':>8} {'StdDev':>8} {'Best':>8} {'Worst':>8} {'AvgIter':>10} {'AvgUpd':>8}")
print("-"*85)

for variant in ['HC', 'SCHC-all', 'SCHC-acp', 'SCHC-imp']:
    if variant not in by_variant:
        continue
    
    results = by_variant[variant]
    
    finals = [r['final'] for r in results]
    improvements = [r['improvement_pct'] for r in results]
    iterations = [r['iterations'] for r in results]
    updates = [r['bound_updates'] for r in results]
    
    avg_final = sum(finals) / len(finals)
    avg_pct = sum(improvements) / len(improvements)
    stddev = (sum((x - avg_final)**2 for x in finals) / len(finals))**0.5
    best = min(finals)
    worst = max(finals)
    avg_iter = sum(iterations) / len(iterations)
    avg_upd = sum(updates) / len(updates)
    
    print(f"{variant:<15} {avg_final:>12.1f} {avg_pct:>7.1f}% {stddev:>8.1f} {best:>8} {worst:>8} {avg_iter:>10.0f} {avg_upd:>8.0f}")

print("="*80)
print()


# ============================================================================
# VARIANT COMPARISON
# ============================================================================

print("="*80)
print("VARIANT HEAD-TO-HEAD COMPARISON")
print("="*80)
print()

hc_results = by_variant['HC']
hc_avg = sum(r['final'] for r in hc_results) / len(hc_results)

for variant in ['SCHC-all', 'SCHC-acp', 'SCHC-imp']:
    if variant not in by_variant:
        continue
    
    schc_results = by_variant[variant]
    schc_avg = sum(r['final'] for r in schc_results) / len(schc_results)
    
    diff = hc_avg - schc_avg
    
    # Win/loss
    wins = sum(1 for hc_r, schc_r in zip(hc_results, schc_results) 
               if schc_r['final'] < hc_r['final'])
    losses = sum(1 for hc_r, schc_r in zip(hc_results, schc_results) 
                 if schc_r['final'] > hc_r['final'])
    ties = len(hc_results) - wins - losses
    
    print(f"HC vs {variant}:")
    print(f"  Average: {hc_avg:.1f} vs {schc_avg:.1f} (Δ={diff:+.1f}, {abs(diff)/hc_avg*100:.1f}%)")
    print(f"  Win/Loss: {wins}W - {losses}L - {ties}T ({wins/len(hc_results)*100:.0f}% win rate)")
    print()

# Compare SCHC variants against each other
print("SCHC Variant Comparison:")
print()

variant_pairs = [
    ('SCHC-all', 'SCHC-acp'),
    ('SCHC-all', 'SCHC-imp'),
    ('SCHC-acp', 'SCHC-imp')
]

for var1, var2 in variant_pairs:
    if var1 not in by_variant or var2 not in by_variant:
        continue
    
    results1 = by_variant[var1]
    results2 = by_variant[var2]
    
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
print(f"All results saved to: {RUN_DIR}")
print(f"Summary CSV: {summary_csv_path}")
print()