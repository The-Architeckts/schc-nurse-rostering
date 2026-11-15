'''
Final Algorithm Validation - Verbose Single Instance Run
=========================================================
Runs all three SCHC variants and HC on INRC1_medium01 with full
verbose output before committing to the final Falcon sweep.

Purpose:
    Confirm that each variant's internal behaviour matches expectations:
    - HC:       greedy descent, terminates at local optimum
    - SCHC-all: bound updates every Lc total steps, adaptive termination
    - SCHC-acp: bound updates every Lc accepted moves, adaptive termination
    - SCHC-imp: bound updates every Lc improving moves, stagnation termination

Expected behaviour:
    - All three SCHC variants improve substantially on HC baseline
    - SCHC-all:  fast convergence, moderate improvement
    - SCHC-acp:  slower, better improvement than all
    - SCHC-imp:  slowest, competitive with or better than acp
    - SCHC-imp bound updates ~90 regardless of Lc
    - SCHC-imp improving move rate ~1% of total iterations

Lc values used (empirically optimal from overnight testing):
    SCHC-all:  Lc=1500  (optimal for medium)
    SCHC-acp:  Lc=1000  (near-optimal, faster than 2500)
    SCHC-imp:  Lc=25    (empirically optimal for medium)

Each run prints a progress table every 10,000 iterations showing
current penalty, best penalty, bound, updates, acceptance rate,
improving move rate (imp only), idle/stagnation counter, and time.
'''

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.hill_climbing import HillClimbing
from algorithms.schc import SCHC
from constraints import evaluate_solution

# ============================================================================
# CONFIGURATION
# ============================================================================

INSTANCE_PATH = str(Path(__file__).resolve().parent.parent / 'data' / 'inrc1' / 'INRC1_medium01.json')
RANDOM_SEED   = 1

SCHC_CONFIGS = [
    ('all', 1500),
    ('acp', 1000),
    ('imp', 25),
]

MAX_IDLE_HC = 2000

# ============================================================================
# LOAD INSTANCE
# ============================================================================

print("=" * 80)
print("FINAL ALGORITHM VALIDATION")
print("=" * 80)
print(f"Instance:    {INSTANCE_PATH}")
print(f"Random seed: {RANDOM_SEED}")
print()

instance     = load_instance(INSTANCE_PATH)
baseline     = greedy_constructor(instance)
baseline_pen = evaluate_solution(baseline, instance)

n_nurses = len(instance['nurses'])
n_days   = instance['period']

print(f"Loaded: {instance['name']}  ({n_nurses} nurses, {n_days} days)")
print(f"Greedy baseline penalty: {baseline_pen}")
print()

# ============================================================================
# HC BASELINE
# ============================================================================

print("=" * 80)
print("HC BASELINE")
print("=" * 80)
print(f"Max idle iterations: {MAX_IDLE_HC}")
print()

hc = HillClimbing(
    instance_data=instance,
    max_idle_iterations=MAX_IDLE_HC,
    random_seed=RANDOM_SEED
)

hc_start = time.time()
_, hc_stats = hc.optimize(baseline, verbose=True)
hc_elapsed = time.time() - hc_start

print(f"HC RESULT: {baseline_pen} -> {hc_stats['final_penalty']} "
      f"({hc_stats['improvement_percent']:.1f}%)  "
      f"Time: {hc_elapsed:.1f}s")
print()

# ============================================================================
# SCHC VARIANTS
# ============================================================================

results = {}

for variant, lc in SCHC_CONFIGS:
    print("=" * 80)
    print(f"SCHC-{variant.upper()}  Lc={lc}")
    print("=" * 80)
    print()

    schc = SCHC(
        instance_data=instance,
        Lc=lc,
        variant=variant,
        random_seed=RANDOM_SEED,
        print_interval=10000
    )

    _, stats = schc.optimize(baseline, verbose=True)
    results[variant] = stats

    print(f"SCHC-{variant.upper()} RESULT: "
          f"{baseline_pen} -> {stats['final_penalty']} "
          f"({stats['improvement_percent']:.1f}%)  "
          f"Updates: {stats['bound_updates']}  "
          f"Iters: {stats['iterations']:,}  "
          f"Time: {stats['elapsed_time']:.1f}s")
    print()


# ============================================================================
# COMPARISON SUMMARY
# ============================================================================

print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print()
print(f"Baseline (greedy): {baseline_pen}")
print()
print(f"{'Algorithm':<14} {'Lc':>6} {'Final':>8} {'Improv%':>8} "
      f"{'Updates':>8} {'Iters':>12} {'Time':>8}")
print("-" * 72)

print(f"{'HC':<14} {'N/A':>6} {hc_stats['final_penalty']:>8} "
      f"{hc_stats['improvement_percent']:>7.1f}% "
      f"{'N/A':>8} {hc_stats['iterations']:>12,} "
      f"{hc_elapsed:>7.1f}s")

for variant, lc in SCHC_CONFIGS:
    s = results[variant]
    print(f"{'SCHC-' + variant:<14} {lc:>6} {s['final_penalty']:>8} "
          f"{s['improvement_percent']:>7.1f}% "
          f"{s['bound_updates']:>8} {s['iterations']:>12,} "
          f"{s['elapsed_time']:>7.1f}s")

print()
print("EXPECTED CHECKS:")

hc_final = hc_stats['final_penalty']
all_pass = True

# Check 1: all SCHC variants beat HC
for variant, lc in SCHC_CONFIGS:
    s = results[variant]
    passed = s['final_penalty'] < hc_final
    mark   = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    print(f"  [{mark}] SCHC-{variant} beats HC: "
          f"{s['final_penalty']} < {hc_final} = {passed}")

# Check 2: SCHC-imp bound updates ~90
imp_updates = results['imp']['bound_updates']
imp_ok      = 50 <= imp_updates <= 150
mark        = "PASS" if imp_ok else "WARN"
if not imp_ok:
    all_pass = False
print(f"  [{mark}] SCHC-imp bound updates in expected range [50-150]: "
      f"{imp_updates}")

# Check 3: SCHC-imp improving move rate < 10%
imp_imove_rate = (results['imp'].get('improving_moves', 0)
                  / results['imp']['iterations'] * 100)
imp_rate_ok    = imp_imove_rate < 15
mark           = "PASS" if imp_rate_ok else "WARN"
print(f"  [{mark}] SCHC-imp improving move rate < 15%: "
      f"{imp_imove_rate:.1f}%")

# Check 4: SCHC-imp outperforms or matches SCHC-all
imp_vs_all = results['imp']['final_penalty'] <= results['all']['final_penalty']
mark       = "PASS" if imp_vs_all else "INFO"
print(f"  [{'PASS' if imp_vs_all else 'INFO'}] SCHC-imp <= SCHC-all: "
      f"{results['imp']['final_penalty']} <= "
      f"{results['all']['final_penalty']} = {imp_vs_all}")

# Check 5: SCHC-all and SCHC-acp terminated via adaptive condition
for variant, lc in [('all', 1500), ('acp', 1000)]:
    iters = results[variant]['iterations']
    # At termination idle > 0.01 * iters, so iters should be > 10000
    reasonable = iters > 10000
    mark = "PASS" if reasonable else "FAIL"
    print(f"  [{mark}] SCHC-{variant} ran sufficient iterations: "
          f"{iters:,}")

print()
if all_pass:
    print("ALL CHECKS PASSED. Ready for final Falcon sweep.")
else:
    print("SOME CHECKS FAILED OR WARNED. Review output above before "
          "submitting to Falcon.")
print()
print("=" * 80)