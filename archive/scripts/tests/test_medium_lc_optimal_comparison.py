'''
MEDIUM INSTANCES - Lc SCALING VALIDATION TEST (POST BUG FIX)

Strategic Lc selection based on sprint results:
- Sprint optimal Lc = 1000 (3.57x problem size)
- Medium problem size ≈ 1400 assignments

Test points:
- Lc=500:  Below sprint optimal, tests performance floor
- Lc=1500: ~1.07x size, slightly above sprint optimal ratio

Goal: Validate Lc scaling pattern and SCHC-acp behavior on larger instances
'''

import sys
import time
from pathlib import Path
from datetime import datetime
import csv

# Add src to path (script runs from src/tests/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.hill_climbing import HillClimbing
from algorithms.schc import SCHC
from constraints import evaluate_solution

# Project root (go up two levels: tests -> src -> root)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration - use relative paths from project root
INSTANCES = [
    f'data/inrc1/INRC1_medium{i:02d}.json' for i in [1, 2, 3, 4, 5]
]

SCHC_VARIANTS = ["all", "acp", "imp"]
LC_VALUES = [500, 1500]
RUNS_PER_CONFIG = 10

# Convergence parameters
MAX_IDLE_HC = 2000
MAX_IDLE_SCHC = 10000

# Convergence parameters
MAX_IDLE_HC = 2000
MAX_IDLE_SCHC = 10000

def calculate_improvement(baseline, final):
    '''Calculate percentage improvement'''
    if baseline == 0:
        return 0.0
    return ((baseline - final) / baseline) * 100

def format_time(seconds):
    '''Format seconds as hours and minutes'''
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    if hours > 0:
        return f"{hours}.{minutes}h"
    return f"{minutes}m"

def main():
    print("=" * 80)
    print("MEDIUM INSTANCES - Lc SCALING VALIDATION (POST BUG FIX)")
    print("=" * 80)
    print(f"Testing {len(INSTANCES)} medium instances")
    print(f"SCHC variants: {SCHC_VARIANTS}")
    print(f"Lc values: {LC_VALUES}")
    print(f"Runs per configuration: {RUNS_PER_CONFIG}")
    print()
    
    # Calculate total runs
    schc_runs = len(INSTANCES) * len(SCHC_VARIANTS) * len(LC_VALUES) * RUNS_PER_CONFIG
    hc_runs = len(INSTANCES) * RUNS_PER_CONFIG
    total_runs = schc_runs + hc_runs
    
    print(f"SCHC runs: {len(INSTANCES)} × {len(SCHC_VARIANTS)} × {len(LC_VALUES)} × {RUNS_PER_CONFIG} = {schc_runs}")
    print(f"HC runs:   {len(INSTANCES)} × {RUNS_PER_CONFIG} = {hc_runs}")
    print(f"Total runs: {total_runs}")
    print()
    
    # Setup output directory in project root
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path('outputs') / f"medium_lc_scaling_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    print("=" * 80)
    print()
    
    # Results storage
    all_results = []
    run_counter = 0
    start_time = time.time()
    
    # Checkpoint file
    checkpoint_file = output_dir / "checkpoint.txt"
    
    for instance_path in INSTANCES:
        if not Path(instance_path).exists():
            print(f"WARNING: Skipping {instance_path} - file not found")
            continue
        
        instance_name = Path(instance_path).stem
        
        print("=" * 80)
        print(f"TESTING: {instance_name}")
        print("=" * 80)
        
        # Load instance
        instance = load_instance(instance_path)
        n_nurses = len(instance['nurses'])
        n_days = instance['period']
        
        print(f"Loaded: {instance_name} ({n_nurses} nurses, {n_days} days)")
        
        # Generate baseline
        baseline = greedy_constructor(instance)
        baseline_penalty = evaluate_solution(baseline, instance)
        print(f"Baseline penalty: {baseline_penalty}")
        print()
        
        # HC baseline
        print(f"  Testing HC (baseline):")
        hc_results = []
        
        for run in range(RUNS_PER_CONFIG):
            run_counter += 1
            elapsed_total = time.time() - start_time
            eta_seconds = (elapsed_total / run_counter) * (total_runs - run_counter)
            eta_str = format_time(eta_seconds)
            
            hc = HillClimbing(
                instance_data=instance,
                max_idle_iterations=MAX_IDLE_HC,
                random_seed=run + 1
            )
            
            best_solution, stats = hc.optimize(baseline, verbose=False)
            final = stats['final_penalty']
            elapsed = stats['elapsed_time']
            improvement = calculate_improvement(baseline_penalty, final)
            hc_results.append(final)
            
            print(f"    Run {run+1}/{RUNS_PER_CONFIG} [{run_counter}/{total_runs}] (ETA: {eta_str})... "
                  f"{baseline_penalty} → {final} ({improvement:.1f}%), Time: {elapsed:.1f}s")
            
            all_results.append({
                'instance': instance_name,
                'algorithm': 'HC',
                'variant': 'N/A',
                'Lc': 0,
                'run': run + 1,
                'baseline': baseline_penalty,
                'final': final,
                'improvement_pct': improvement,
                'bound_updates': 0,
                'time': elapsed
            })
        
        hc_avg = sum(hc_results) / len(hc_results)
        print()
        
        # SCHC variants
        for variant in SCHC_VARIANTS:
            for Lc in LC_VALUES:
                print(f"  Testing SCHC-{variant} (Lc={Lc}):")
                
                for run in range(RUNS_PER_CONFIG):
                    run_counter += 1
                    elapsed_total = time.time() - start_time
                    eta_seconds = (elapsed_total / run_counter) * (total_runs - run_counter)
                    eta_str = format_time(eta_seconds)
                    
                    schc = SCHC(
                        instance_data=instance,
                        Lc=Lc,
                        variant=variant,
                        max_idle_iterations=MAX_IDLE_SCHC,
                        random_seed=run + 1
                    )
                    
                    best_solution, stats = schc.optimize(baseline, verbose=False)
                    final = stats['final_penalty']
                    elapsed = stats['elapsed_time']
                    updates = stats['bound_updates']
                    improvement = calculate_improvement(baseline_penalty, final)
                    
                    print(f"    Run {run+1}/{RUNS_PER_CONFIG} [{run_counter}/{total_runs}] (ETA: {eta_str})... "
                          f"{baseline_penalty} → {final} ({improvement:.1f}%), "
                          f"Updates: {updates}, Time: {elapsed:.1f}s")
                    
                    all_results.append({
                        'instance': instance_name,
                        'algorithm': 'SCHC',
                        'variant': variant,
                        'Lc': Lc,
                        'run': run + 1,
                        'baseline': baseline_penalty,
                        'final': final,
                        'improvement_pct': improvement,
                        'bound_updates': updates,
                        'time': elapsed
                    })
                
                print()
        
        # Save checkpoint
        with open(checkpoint_file, 'a') as f:
            f.write(f"Completed: {instance_name} at {datetime.now()}\n")
    
    # Save detailed results
    csv_file = output_dir / "detailed_results.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)
    
    print("=" * 80)
    print("ANALYSIS: Lc SCALING BY VARIANT")
    print("=" * 80)
    print()
    
    # Analyze by variant and Lc
    summary = []
    
    for variant in SCHC_VARIANTS:
        print(f"SCHC-{variant} - Lc Scaling:")
        print("Lc      Avg Final    Avg %   StdDev   Best  Worst   AvgUpd   AvgTime  Lc/Size")
        print("-" * 80)
        
        for Lc in LC_VALUES:
            filtered = [r for r in all_results 
                       if r['algorithm'] == 'SCHC' 
                       and r['variant'] == variant 
                       and r['Lc'] == Lc]
            
            if filtered:
                finals = [r['final'] for r in filtered]
                improvements = [r['improvement_pct'] for r in filtered]
                updates = [r['bound_updates'] for r in filtered]
                times = [r['time'] for r in filtered]
                
                avg_final = sum(finals) / len(finals)
                avg_improvement = sum(improvements) / len(improvements)
                std_dev = (sum((x - avg_final) ** 2 for x in finals) / len(finals)) ** 0.5
                best = min(finals)
                worst = max(finals)
                avg_updates = sum(updates) / len(updates)
                avg_time = sum(times) / len(times)
                
                # Approximate Lc/Size ratio (medium instances ~1400 assignments)
                lc_size_ratio = Lc / 1400
                
                print(f"{Lc:4d}    {avg_final:8.1f}  {avg_improvement:6.1f}%  {std_dev:6.1f}  "
                      f"{best:4d}  {worst:4d}  {avg_updates:7.1f}  {avg_time:7.1f}s  {lc_size_ratio:6.2f}")
                
                summary.append({
                    'variant': variant,
                    'Lc': Lc,
                    'avg_final': avg_final,
                    'avg_improvement': avg_improvement,
                    'std_dev': std_dev,
                    'best': best,
                    'worst': worst,
                    'avg_updates': avg_updates,
                    'avg_time': avg_time,
                    'lc_size_ratio': lc_size_ratio
                })
        
        print()
    
    # HC baseline
    hc_filtered = [r for r in all_results if r['algorithm'] == 'HC']
    if hc_filtered:
        hc_finals = [r['final'] for r in hc_filtered]
        hc_improvements = [r['improvement_pct'] for r in hc_filtered]
        hc_times = [r['time'] for r in hc_filtered]
        
        hc_avg_final = sum(hc_finals) / len(hc_finals)
        hc_avg_improvement = sum(hc_improvements) / len(hc_improvements)
        hc_avg_time = sum(hc_times) / len(hc_times)
        
        print(f"HC Baseline: Avg={hc_avg_final:.1f}, Improvement={hc_avg_improvement:.1f}%, "
              f"Time={hc_avg_time:.1f}s")
        print()
    
    # Save summary
    summary_file = output_dir / "summary.csv"
    with open(summary_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)
    
    # Identify optimal Lc per variant
    print("=" * 80)
    print("OPTIMAL Lc IDENTIFICATION (MEDIUM INSTANCES)")
    print("=" * 80)
    print()
    
    for variant in SCHC_VARIANTS:
        variant_results = [s for s in summary if s['variant'] == variant]
        optimal = min(variant_results, key=lambda x: x['avg_final'])
        
        print(f"SCHC-{variant}:  Optimal Lc = {optimal['Lc']}  "
              f"(avg penalty: {optimal['avg_final']:.1f}, ratio: {optimal['lc_size_ratio']:.2f})")
        
        for result in sorted(variant_results, key=lambda x: x['Lc']):
            delta = result['avg_final'] - optimal['avg_final']
            marker = "☆" if result['Lc'] == optimal['Lc'] else " "
            print(f"  {marker} Lc={result['Lc']:4d}:  {result['avg_final']:6.1f}  "
                  f"(+{delta:4.1f} from optimal, ratio: {result['lc_size_ratio']:.2f})")
        print()
    
    # Compare to sprint results
    print("=" * 80)
    print("SCALING COMPARISON: SPRINT vs MEDIUM")
    print("=" * 80)
    print()
    print("Sprint results (size ~280):")
    print("  SCHC-all: Optimal Lc=1000 (ratio: 3.57)")
    print("  SCHC-acp: Lc-insensitive")
    print("  SCHC-imp: Optimal Lc=1000 (ratio: 3.57)")
    print()
    print("Medium results (size ~1400):")
    
    for variant in SCHC_VARIANTS:
        variant_results = [s for s in summary if s['variant'] == variant]
        optimal = min(variant_results, key=lambda x: x['avg_final'])
        print(f"  SCHC-{variant}: Optimal Lc={optimal['Lc']} (ratio: {optimal['lc_size_ratio']:.2f})")
    
    print()
    
    # Final statistics
    total_elapsed = time.time() - start_time
    print("=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print(f"Total runtime: {format_time(total_elapsed)} ({total_elapsed/60:.1f} minutes)")
    print(f"Total runs completed: {total_runs}")
    print(f"Average time per run: {total_elapsed/total_runs:.1f}s")
    print()
    print(f"Results saved to: {output_dir}")
    print(f"Summary CSV:      {summary_file}")
    print(f"Detailed CSV:     {csv_file}")
    print(f"Checkpoint log:   {checkpoint_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()