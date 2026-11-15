import sys
sys.path.insert(0, 'src')
from data_loader import load_instance
from constructors import greedy_constructor
from algorithms.schc import SCHC
from constraints import evaluate_solution

instance = load_instance('data/inrc1/INRC1_medium01.json')
baseline = greedy_constructor(instance)
penalty  = evaluate_solution(baseline, instance)

schc = SCHC(instance_data=instance, Lc=50, variant='imp', random_seed=1)
_, stats = schc.optimize(baseline, verbose=False)
print(f"SCHC-imp Lc=50: {penalty} -> {stats['final_penalty']} "
      f"({stats['improvement_percent']:.1f}%) "
      f"Updates: {stats['bound_updates']} "
      f"Iters: {stats['iterations']} "
      f"Time: {stats['elapsed_time']:.1f}s")
