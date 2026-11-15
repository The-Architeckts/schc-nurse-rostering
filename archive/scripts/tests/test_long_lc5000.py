'''
Test SCHC with Lc=5000 on long instances to find diminishing returns point.
Supervisor requested to test extreme Lc value.

Configuration:
- 5 long instances
- 3 SCHC variants (all, acp, imp)
- ONLY Lc=5000 (testing extreme exploration)
- 5 runs per config = 75 SCHC runs + 25 HC = 100 runs
- Estimated runtime: 8-10 hours
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

INSTANCES = [f'data/inrc1/INRC1_long{i:02d}.json' for i in range(1, 6)]
VARIANTS = ['all', 'acp', 'imp']
LC_VALUE = 5000  # EXTREME Lc value
NUM_RUNS = 5

MAX_IDLE_HC = 2000

MAX_IDLE_SCHC = 10000

OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_DIR = OUTPUT_DIR / f'long_lc5000_{TIMESTAMP}'
RUN_DIR.mkdir(exist_ok=True)

CHECKPOINT_FILE = RUN_DIR / 'checkpoint.txt'

print("="*80)
print("LONG INSTANCES - Lc=5000 EXTREME EXPLORATION TEST")
print("="*80)
print(f"Testing {len(INSTANCES)} long instances")
print(f"SCHC variants: {VARIANTS}")
print(f"Lc value: {LC_VALUE} (EXTREME)")
print(f"Runs per configuration: {NUM_RUNS}")
print()
print(f"SCHC runs: {len(INSTANCES)} × {len(VARIANTS)} × {NUM_RUNS} = {len(INSTANCES) * len(VARIANTS) * NUM_RUNS}")
print(f"HC runs: {len(INSTANCES)} × {NUM_RUNS} = {len(INSTANCES) * NUM_RUNS}")
print(f"Total runs: {len(INSTANCES) * (len(VARIANTS) + 1) * NUM_RUNS}")
print()
print(f"Output directory: {RUN_DIR}")
print()


def save_checkpoint(message):
    '''Save progress checkpoint.'''
    with open(CHECKPOINT_FILE, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")


# ============================================================================
# MAIN TESTING LOOP
# ============================================================================

all_results = []

summary_csv_path = RUN_DIR / 'summary.csv'
csv_file = open(summary_csv_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'Instance', 'Algorithm', 'Lc', 'Run', 'Nurses', 'Days', 'Baseline', 'Final', 
    'Improvement', 'Improvement_Pct', 'Iterations', 'Bound_Updates', 'Time'
])

total_start_time = time.time()
completed_runs = 0
total_runs = len(INSTANCES) * (len(VARIANTS) + 1) * NUM_RUNS

save_checkpoint(f"Starting Lc=5000 test - {total_runs} total runs")

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
    
    try:
        instance = load_instance(instance_path)
        n_nurses = len(instance['nurses'])
        n_days = instance['period']
        print(f"Loaded: {instance['name']} ({n_nurses} nurses, {n_days} days)")
    except Exception as e:
        print(f"ERROR loading: {e}")
        save_checkpoint(f"Error loading {instance_name}: {e}")
        continue
    
    baseline = greedy_constructor(instance)
    baseline_penalty = evaluate_solution(baseline, instance)
    print(f"Baseline penalty: {baseline_penalty}")
    print()
    
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
            'baseline': baseline_penalty,
            'final': stats['final_penalty'],
            'improvement_pct': stats['improvement_percent'],
            'time': stats['elapsed_time']
        })
        
        print(f"{baseline_penalty} → {stats['final_penalty']} "
              f"({stats['improvement_percent']:.1f}%), Time: {stats['elapsed_time']:.1f}s")
    
    print()
    
    # Test each SCHC variant with Lc=5000
    for variant in VARIANTS:
        print(f"  Testing SCHC-{variant} (Lc={LC_VALUE}):")
        
        for run in range(1, NUM_RUNS + 1):
            completed_runs += 1
            elapsed_total = time.time() - total_start_time
            eta_seconds = (elapsed_total / completed_runs) * (total_runs - completed_runs)
            eta_hours = eta_seconds / 3600
            
            print(f"    Run {run}/{NUM_RUNS} [{completed_runs}/{total_runs}] "
                  f"(ETA: {eta_hours:.1f}h)...", end=" ", flush=True)
            
            schc = SCHC(
                instance_data=instance,
                Lc=LC_VALUE,
                variant=variant,
                max_idle_iterations=MAX_IDLE_SCHC,
                random_seed=run
            )
            
            best_solution, stats = schc.optimize(baseline, verbose=False)
            
            csv_writer.writerow([
                instance_name, f'SCHC-{variant}', LC_VALUE, run, n_nurses, n_days,
                baseline_penalty, stats['final_penalty'], stats['improvement'],
                stats['improvement_percent'], stats['iterations'],
                stats['bound_updates'], stats['elapsed_time']
            ])
            
            result = {
                'instance': instance_name,
                'algorithm': f'SCHC-{variant}',
                'lc': LC_VALUE,
                'run': run,
                'baseline': baseline_penalty,
                'final': stats['final_penalty'],
                'improvement_pct': stats['improvement_percent'],
                'iterations': stats['iterations'],
                'bound_updates': stats['bound_updates'],
                'time': stats['elapsed_time']
            }
            all_results.append(result)
            
            print(f"{baseline_penalty} → {stats['final_penalty']} "
                  f"({stats['improvement_percent']:.1f}%), "
                  f"Updates: {stats['bound_updates']}, "
                  f"Time: {stats['elapsed_time']:.1f}s")
        
        print()
    
    instance_elapsed = time.time() - instance_start
    save_checkpoint(f"Completed {instance_name} in {instance_elapsed/60:.1f} minutes")
    print(f"{instance_name} complete in {instance_elapsed/60:.1f} minutes")
    print()

csv_file.close()

total_elapsed = time.time() - total_start_time
save_checkpoint(f"Testing complete - {total_elapsed/3600:.2f} hours")


# ============================================================================
# ANALYSIS
# ============================================================================

print("="*80)
print("ANALYSIS: Lc=5000 RESULTS")
print("="*80)
print()

by_variant = defaultdict(list)
for result in all_results:
    if result['algorithm'] == 'HC':
        by_variant['HC'].append(result)
    else:
        by_variant[result['algorithm']].append(result)

# HC baseline
hc_results = by_variant['HC']
hc_avg = sum(r['final'] for r in hc_results) / len(hc_results)
hc_pct = sum(r['improvement_pct'] for r in hc_results) / len(hc_results)

print("HC BASELINE:")
print(f"  Average final: {hc_avg:.1f}")
print(f"  Average improvement: {hc_pct:.1f}%")
print()

# SCHC variants
print(f"{'Variant':<15} {'Avg Final':>12} {'Avg %':>8} {'StdDev':>8} {'vs HC':>8} {'AvgTime':>10}")
print("-"*75)

for variant in VARIANTS:
    key = f'SCHC-{variant}'
    if key not in by_variant:
        continue
    
    results = by_variant[key]
    finals = [r['final'] for r in results]
    improvements = [r['improvement_pct'] for r in results]
    times = [r['time'] for r in results]
    
    avg_final = sum(finals) / len(finals)
    avg_pct = sum(improvements) / len(improvements)
    stddev = (sum((x - avg_final)**2 for x in finals) / len(finals))**0.5
    vs_hc = avg_final - hc_avg
    avg_time = sum(times) / len(times)
    
    print(f"{key:<15} {avg_final:>12.1f} {avg_pct:>7.1f}% {stddev:>8.1f} {vs_hc:>+7.1f} {avg_time:>9.1f}s")

print()

# Find best variant
best_variant = min([(k, sum(r['final'] for r in v)/len(v)) 
                    for k, v in by_variant.items() if k != 'HC'],
                   key=lambda x: x[1])

print(f"☆ BEST VARIANT: {best_variant[0]} (avg: {best_variant[1]:.1f})")
print()

print("="*80)
print("TESTING COMPLETE")
print("="*80)
print()
print(f"Total runtime: {total_elapsed/3600:.2f} hours")
print(f"Total runs completed: {completed_runs}")
print(f"Average time per run: {total_elapsed/completed_runs:.1f}s")
print()
print(f"All results saved to: {RUN_DIR}")
print(f"Summary CSV: {summary_csv_path}")
print(f"Checkpoint log: {CHECKPOINT_FILE}")
print("="*80)