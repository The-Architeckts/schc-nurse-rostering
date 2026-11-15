'''
SCHC Bug Investigation and Fix Validation
Run on sprint instances for speed.
'''

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
import time
from operators import get_all_operators
from constraints import evaluate_solution
from data_loader import load_instance
from constructors import greedy_constructor


class SCHC_Debug:
    '''
    Instrumented SCHC exposing two suspected bugs:
    
    Bug 1 (acp): Bound updates on EVERY acceptance instead of every Lc acceptances.
                 Result: Lc has zero effect on acp behaviour.
    
    Bug 2 (imp): is_new_best check runs AFTER self.best_penalty is already updated,
                 so the condition is always False.
                 Result: imp improvement trigger never fires, only fallback Lc fires.
    '''

    def __init__(self, instance_data, Lc=100, variant='all',
                 max_idle_iterations=5000, random_seed=None, use_fix=False):
        self.instance_data = instance_data
        self.Lc = Lc
        self.variant = variant
        self.max_idle_iterations = max_idle_iterations
        self.operators = get_all_operators()
        self.use_fix = use_fix

        if random_seed is not None:
            random.seed(random_seed)

        self.iterations = 0
        self.accepted_moves = 0
        self.rejected_moves = 0
        self.idle_iterations = 0
        self.best_penalty = float('inf')
        self.bound_updates = 0
        self.operator_statistics = {i: {'attempts': 0, 'accepted': 0}
                                    for i in range(len(self.operators))}

        # Debug tracking
        self.bound_update_reasons = {
            'improvement_trigger': 0,
            'fallback_lc': 0,
            'acceptance_trigger': 0
        }
        self.max_step_counter_seen = 0
        self.counter_at_reset = []

    def optimize(self, initial_solution, verbose=False):
        start_time = time.time()

        current_solution = initial_solution.copy()
        current_penalty = evaluate_solution(current_solution, self.instance_data)
        best_solution = current_solution.copy()
        self.best_penalty = current_penalty

        cost_bound = current_penalty
        step_counter = 0
        penalty_history = [current_penalty]

        while self.idle_iterations < self.max_idle_iterations:
            self.iterations += 1

            operator_idx = random.randint(0, len(self.operators) - 1)
            operator = self.operators[operator_idx]
            self.operator_statistics[operator_idx]['attempts'] += 1

            neighbor = operator(current_solution, self.instance_data)

            if neighbor is None:
                if self.variant == 'all':
                    step_counter += 1
                    self.max_step_counter_seen = max(self.max_step_counter_seen, step_counter)
                    if step_counter >= self.Lc:
                        self.counter_at_reset.append(step_counter)
                        cost_bound = current_penalty
                        step_counter = 0
                        self.bound_updates += 1
                        self.bound_update_reasons['fallback_lc'] += 1
                elif not self.use_fix:
                    # Buggy: acp and imp also increment on null moves in original
                    step_counter += 1
                    self.max_step_counter_seen = max(self.max_step_counter_seen, step_counter)
                    if step_counter >= self.Lc:
                        self.counter_at_reset.append(step_counter)
                        cost_bound = current_penalty
                        step_counter = 0
                        self.bound_updates += 1
                        self.bound_update_reasons['fallback_lc'] += 1
                continue

            neighbor_penalty = evaluate_solution(neighbor, self.instance_data)

            # CRITICAL: capture is_new_best BEFORE updating self.best_penalty
            # In the buggy version this check happens after the update, so always False
            is_new_best_before_update = neighbor_penalty < self.best_penalty

            move_accepted = False
            if neighbor_penalty < cost_bound:
                current_solution = neighbor
                current_penalty = neighbor_penalty
                self.accepted_moves += 1
                self.operator_statistics[operator_idx]['accepted'] += 1
                self.idle_iterations = 0
                move_accepted = True

                if is_new_best_before_update:
                    best_solution = neighbor.copy()
                    self.best_penalty = neighbor_penalty
            else:
                self.rejected_moves += 1
                self.idle_iterations += 1

            # VARIANT BOUND UPDATE LOGIC
            if self.variant == 'all':
                step_counter += 1
                self.max_step_counter_seen = max(self.max_step_counter_seen, step_counter)
                if step_counter >= self.Lc:
                    self.counter_at_reset.append(step_counter)
                    cost_bound = current_penalty
                    step_counter = 0
                    self.bound_updates += 1
                    self.bound_update_reasons['fallback_lc'] += 1

            elif self.variant == 'acp':
                if self.use_fix:
                    # FIXED: count Lc accepted moves before updating bound
                    if move_accepted:
                        step_counter += 1
                        self.max_step_counter_seen = max(self.max_step_counter_seen, step_counter)
                        if step_counter >= self.Lc:
                            self.counter_at_reset.append(step_counter)
                            cost_bound = current_penalty
                            step_counter = 0
                            self.bound_updates += 1
                            self.bound_update_reasons['acceptance_trigger'] += 1
                else:
                    # BUGGY: updates on every single acceptance, counter always 0
                    if move_accepted:
                        self.counter_at_reset.append(step_counter)
                        cost_bound = current_penalty
                        step_counter = 0
                        self.bound_updates += 1
                        self.bound_update_reasons['acceptance_trigger'] += 1
                    else:
                        step_counter += 1
                        self.max_step_counter_seen = max(self.max_step_counter_seen, step_counter)
                        if step_counter >= self.Lc:
                            self.counter_at_reset.append(step_counter)
                            cost_bound = current_penalty
                            step_counter = 0
                            self.bound_updates += 1
                            self.bound_update_reasons['fallback_lc'] += 1

            elif self.variant == 'imp':
                if self.use_fix:
                    # FIXED: use is_new_best captured before self.best_penalty update
                    if is_new_best_before_update:
                        self.counter_at_reset.append(step_counter)
                        cost_bound = current_penalty
                        step_counter = 0
                        self.bound_updates += 1
                        self.bound_update_reasons['improvement_trigger'] += 1
                    else:
                        step_counter += 1
                        self.max_step_counter_seen = max(self.max_step_counter_seen, step_counter)
                        if step_counter >= self.Lc:
                            self.counter_at_reset.append(step_counter)
                            cost_bound = current_penalty
                            step_counter = 0
                            self.bound_updates += 1
                            self.bound_update_reasons['fallback_lc'] += 1
                else:
                    # BUGGY: self.best_penalty already updated above, so this is always False
                    if neighbor_penalty < self.best_penalty:
                        cost_bound = current_penalty
                        step_counter = 0
                        self.bound_updates += 1
                        self.bound_update_reasons['improvement_trigger'] += 1
                    else:
                        step_counter += 1
                        self.max_step_counter_seen = max(self.max_step_counter_seen, step_counter)
                        if step_counter >= self.Lc:
                            self.counter_at_reset.append(step_counter)
                            cost_bound = current_penalty
                            step_counter = 0
                            self.bound_updates += 1
                            self.bound_update_reasons['fallback_lc'] += 1

            if self.iterations % 10 == 0:
                penalty_history.append(current_penalty)

        elapsed = time.time() - start_time
        return best_solution, {
            'initial_penalty': penalty_history[0],
            'final_penalty': self.best_penalty,
            'improvement_percent': (penalty_history[0] - self.best_penalty) / penalty_history[0] * 100,
            'bound_updates': self.bound_updates,
            'bound_update_reasons': self.bound_update_reasons,
            'max_step_counter_seen': self.max_step_counter_seen,
            'counter_at_reset_sample': self.counter_at_reset[:10],
            'accepted_moves': self.accepted_moves,
            'elapsed_time': elapsed,
        }


def run_debug_comparison(instance_data, instance_name, Lc_values, runs=3):
    print("=" * 80)
    print(f"BUG INVESTIGATION: {instance_name}")
    print("=" * 80)

    baseline = greedy_constructor(instance_data)

    results = {}

    for variant in ['acp', 'imp']:
        results[variant] = {}
        for use_fix in [False, True]:
            label = 'FIXED' if use_fix else 'BUGGY'
            results[variant][label] = {}

            for Lc in Lc_values:
                run_results = []
                for run in range(runs):
                    algo = SCHC_Debug(
                        instance_data, Lc=Lc, variant=variant,
                        max_idle_iterations=5000,
                        random_seed=42 + run,
                        use_fix=use_fix
                    )
                    _, stats = algo.optimize(baseline.copy(), verbose=False)
                    run_results.append(stats)

                avg_penalty   = sum(r['final_penalty'] for r in run_results) / runs
                avg_updates   = sum(r['bound_updates'] for r in run_results) / runs
                avg_imp       = sum(r['bound_update_reasons']['improvement_trigger'] for r in run_results) / runs
                avg_acp       = sum(r['bound_update_reasons']['acceptance_trigger'] for r in run_results) / runs
                avg_fallback  = sum(r['bound_update_reasons']['fallback_lc'] for r in run_results) / runs
                max_counter   = max(r['max_step_counter_seen'] for r in run_results)
                sample_resets = run_results[0]['counter_at_reset_sample']

                results[variant][label][Lc] = avg_penalty

                print(f"\n  {variant.upper()} [{label}] Lc={Lc}:")
                print(f"    Avg final penalty:      {avg_penalty:.1f}")
                print(f"    Avg bound updates:      {avg_updates:.1f}")
                print(f"    Acceptance triggers:    {avg_acp:.1f}")
                print(f"    Improvement triggers:   {avg_imp:.1f}")
                print(f"    Fallback (Lc) triggers: {avg_fallback:.1f}")
                print(f"    Max step counter seen:  {max_counter}")
                print(f"    Counter values at reset (first 5): {sample_resets[:5]}")

        print(f"\n  --- Lc SENSITIVITY SUMMARY for {variant.upper()} ---")
        for label in ['BUGGY', 'FIXED']:
            penalties = [results[variant][label][Lc] for Lc in Lc_values]
            spread = max(penalties) - min(penalties)
            print(f"  {label}: {[f'Lc={lc}:{p:.1f}' for lc, p in zip(Lc_values, penalties)]}  spread={spread:.1f}")

    print("\n" + "=" * 80)
    print("WHAT TO LOOK FOR:")
    print("  acp BUGGY: acceptance_triggers == bound_updates, max_counter ~0, identical penalties across Lc")
    print("  acp FIXED: acceptance_triggers == bound_updates, max_counter reaches Lc, penalties differ across Lc")
    print("  imp BUGGY: improvement_triggers == 0, only fallback fires")
    print("  imp FIXED: improvement_triggers > 0, fallback fires much less")
    print("=" * 80)


if __name__ == '__main__':
    Lc_values = [50, 150, 300]

    sprint_paths = [
        'data/inrc1/INRC1_sprint01.json',
        'data/inrc1/INRC1_sprint02.json',
        'data/sprint/INRC1_sprint01.json',
        'data/sprint/INRC1_sprint02.json',
    ]

    loaded = False
    for path in sprint_paths:
        if Path(path).exists():
            instance_data = load_instance(path)
            name = Path(path).stem
            run_debug_comparison(instance_data, name, Lc_values, runs=3)
            loaded = True
            break

    if not loaded:
        print("No sprint instance found. Tried:")
        for p in sprint_paths:
            print(f"  {p}")
        print("Update sprint_paths in the script to match your data directory.")