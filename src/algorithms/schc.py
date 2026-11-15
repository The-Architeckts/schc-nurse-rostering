'''
Step Counting Hill Climbing (SCHC) algorithm for Nurse Rostering Problem.

Based on: Bykov, Y., & Petrovic, S. (2016).
"A Step Counting Hill Climbing Algorithm applied to University Examination Timetabling."
Journal of Scheduling, 19(4), 479-492. doi:10.1007/s10951-016-0469-x

Implements three variants:
- SCHC-all: Update bound after every Lc total steps
- SCHC-acp: Update bound after every Lc accepted moves
- SCHC-imp: Update bound after every Lc improving moves (C(s*) < C(s))

=============================================================================
DESIGN NOTES
=============================================================================

STEP COUNTER (variant-specific, per Figures 1-3 of Bykov & Petrovic 2016):
    SCHC-all: increments on every iteration (including failed operators)
    SCHC-acp: increments on every accepted move
    SCHC-imp: increments only on improving moves (neighbor < current)

IDLE TRACKING (uniform across all variants):
    Idle resets on any accepted move.
    Idle increments on any rejection.
    Rationale: Bykov & Petrovic state the variants differ "by their counting
    mechanisms only." The counting mechanism is the step counter, not the
    termination condition. Uniform idle tracking produces consistent
    termination behaviour as each variant's bound tightens progressively.

TERMINATION:

    SCHC-all and SCHC-acp use the paper's adaptive condition
    (Bykov & Petrovic 2016, Section 3.2):
        Stop when: idle > 100 AND idle > 0.01 * total_iterations

    SCHC-imp uses stagnation-based termination:
        Stop when: iterations since last new best >= max(30000, Lc * 500)

    Rationale for SCHC-imp adaptation: on the NRP, improving moves
    represent only 1-10% of total iterations. The bound tightens
    far more slowly than for all/acp, causing the adaptive idle condition
    to require millions of iterations to fire. Empirical monitoring of
    medium01 established that the maximum gap between successive new best
    improvements is approximately 80,000 iterations at Lc=50. The
    stagnation limit of max(30000, Lc*500) provides a comfortable margin:
        Lc=25:  30,000 stagnation limit
        Lc=50:  30,000 stagnation limit
        Lc=100: 50,000 stagnation limit
        Lc=150: 75,000 stagnation limit
        Lc=500: 250,000 stagnation limit

VERBOSE OUTPUT:
    When verbose=True, prints a header and a progress line every
    print_interval iterations showing:
        Iter, Current penalty, Best penalty, Bound, Updates,
        Acceptance rate, Improving move rate (imp only), Idle, Time,
        and the termination threshold.
    This matches the monitored output used during algorithm development
    and allows real-time inspection of convergence behaviour.
=============================================================================
'''

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
import time
from operators import get_all_operators
from constraints import evaluate_solution


class SCHC:
    '''
    Step Counting Hill Climbing with configurable variants.

    Parameters:
        instance_data  : loaded INRC-I instance dict
        Lc             : counter limit (single parameter per Bykov & Petrovic)
        variant        : 'all', 'acp', or 'imp'
        random_seed    : integer seed for reproducibility
        print_interval : iterations between progress lines when verbose=True
                         (default 10000; set higher for long runs)
    '''

    VALID_VARIANTS = ['all', 'acp', 'imp']

    def __init__(self, instance_data, Lc=100, variant='all',
                 random_seed=None, print_interval=10000):
        if variant not in self.VALID_VARIANTS:
            raise ValueError(
                f"Invalid variant '{variant}'. "
                f"Must be one of {self.VALID_VARIANTS}"
            )

        self.instance_data  = instance_data
        self.Lc             = Lc
        self.variant        = variant
        self.print_interval = print_interval
        self.operators      = get_all_operators()

        if random_seed is not None:
            random.seed(random_seed)

        self.iterations                   = 0
        self.accepted_moves               = 0
        self.rejected_moves               = 0
        self.improving_moves              = 0
        self.idle_iterations              = 0
        self.iters_since_best_improvement = 0
        self.best_penalty                 = float('inf')
        self.penalty_history              = []
        self.bound_updates                = 0
        self.operator_statistics          = {
            i: {'attempts': 0, 'accepted': 0}
            for i in range(len(self.operators))
        }

    def _stagnation_limit(self):
        return max(30000, self.Lc * 500)

    def _converged(self):
        if self.variant == 'imp':
            return (self.iters_since_best_improvement
                    >= self._stagnation_limit())
        else:
            return (self.idle_iterations > 100 and
                    self.idle_iterations > 0.01 * self.iterations)

    def _print_header(self):
        if self.variant == 'imp':
            print(f"{'Iter':>10} {'Current':>8} {'Best':>6} {'Bound':>6} "
                  f"{'Updates':>8} {'AccRate':>8} {'ImpRate':>8} "
                  f"{'Stagnation':>11} {'Time':>8}  (limit)")
            print("-" * 96)
        else:
            print(f"{'Iter':>10} {'Current':>8} {'Best':>6} {'Bound':>6} "
                  f"{'Updates':>8} {'AccRate':>8} "
                  f"{'Idle':>7} {'Time':>8}  (threshold)")
            print("-" * 80)

    def _print_progress(self, cost_bound, start_time):
        elapsed  = time.time() - start_time
        acc_rate = self.accepted_moves / self.iterations * 100

        if self.variant == 'imp':
            imp_rate = self.improving_moves / self.iterations * 100
            limit    = self._stagnation_limit()
            print(
                f"{self.iterations:>10} "
                f"{self.penalty_history[-1] if self.penalty_history else 0:>8} "
                f"{self.best_penalty:>6} "
                f"{cost_bound:>6} "
                f"{self.bound_updates:>8} "
                f"{acc_rate:>7.1f}% "
                f"{imp_rate:>7.1f}% "
                f"{self.iters_since_best_improvement:>11,} "
                f"{elapsed:>7.1f}s  "
                f"({limit:,})",
                flush=True
            )
        else:
            threshold = 0.01 * self.iterations
            print(
                f"{self.iterations:>10} "
                f"{self.penalty_history[-1] if self.penalty_history else 0:>8} "
                f"{self.best_penalty:>6} "
                f"{cost_bound:>6} "
                f"{self.bound_updates:>8} "
                f"{acc_rate:>7.1f}% "
                f"{self.idle_iterations:>7} "
                f"{elapsed:>7.1f}s  "
                f"({threshold:.0f})",
                flush=True
            )

    def optimize(self, initial_solution, verbose=True):
        start_time        = time.time()
        current_solution  = initial_solution.copy()
        current_penalty   = evaluate_solution(current_solution, self.instance_data)
        best_solution     = current_solution.copy()
        self.best_penalty = current_penalty

        cost_bound   = current_penalty
        step_counter = 0

        self.iters_since_best_improvement = 0
        self.penalty_history.append(current_penalty)

        if verbose:
            print("=" * 80)
            print(f"STEP COUNTING HILL CLIMBING (SCHC-{self.variant})")
            print("=" * 80)
            print(f"Initial penalty:     {current_penalty}")
            print(f"Variant:             {self.variant}")
            print(f"Counter limit (Lc):  {self.Lc}")
            if self.variant == 'imp':
                print(f"Termination:         stagnation "
                      f"(no new best for {self._stagnation_limit():,} iters)")
            else:
                print(f"Termination:         adaptive "
                      f"(idle > max(100, 0.01 * total))")
            print(f"Available operators: {len(self.operators)}")
            print()
            self._print_header()

        while not self._converged():
            self.iterations                   += 1
            self.iters_since_best_improvement += 1

            operator_idx = random.randint(0, len(self.operators) - 1)
            operator     = self.operators[operator_idx]
            self.operator_statistics[operator_idx]['attempts'] += 1

            neighbor = operator(current_solution, self.instance_data)

            if neighbor is None:
                if self.variant == 'all':
                    step_counter += 1
                    if step_counter >= self.Lc:
                        cost_bound   = current_penalty
                        step_counter = 0
                        self.bound_updates += 1
                self.idle_iterations += 1
                continue

            neighbor_penalty = evaluate_solution(neighbor, self.instance_data)

            is_improving = neighbor_penalty < current_penalty
            is_new_best  = neighbor_penalty < self.best_penalty

            # ------------------------------------------------------------------
            # ACCEPTANCE: strictly below cost bound
            # ------------------------------------------------------------------
            move_accepted = False
            if neighbor_penalty < cost_bound:
                current_solution = neighbor
                current_penalty  = neighbor_penalty
                self.accepted_moves += 1
                self.operator_statistics[operator_idx]['accepted'] += 1
                move_accepted = True

                if is_improving:
                    self.improving_moves += 1

                if is_new_best:
                    best_solution                     = neighbor.copy()
                    self.best_penalty                 = neighbor_penalty
                    self.iters_since_best_improvement = 0

            else:
                self.rejected_moves += 1

            # ------------------------------------------------------------------
            # IDLE TRACKING (uniform across all variants)
            # ------------------------------------------------------------------
            if move_accepted:
                self.idle_iterations = 0
            else:
                self.idle_iterations += 1

            # ------------------------------------------------------------------
            # VARIANT-SPECIFIC STEP COUNTER AND BOUND UPDATE
            # ------------------------------------------------------------------
            if self.variant == 'all':
                step_counter += 1
                if step_counter >= self.Lc:
                    cost_bound   = current_penalty
                    step_counter = 0
                    self.bound_updates += 1

            elif self.variant == 'acp':
                if move_accepted:
                    step_counter += 1
                    if step_counter >= self.Lc:
                        cost_bound   = current_penalty
                        step_counter = 0
                        self.bound_updates += 1

            elif self.variant == 'imp':
                if is_improving:
                    step_counter += 1
                    if step_counter >= self.Lc:
                        cost_bound   = current_penalty
                        step_counter = 0
                        self.bound_updates += 1

            if self.iterations % 100 == 0:
                self.penalty_history.append(current_penalty)

            if verbose and self.iterations % self.print_interval == 0:
                self._print_progress(cost_bound, start_time)

        elapsed_time = time.time() - start_time

        # Final progress line
        if verbose:
            self._print_progress(cost_bound, start_time)
            print()
            print("=" * 80)
            print("OPTIMIZATION COMPLETE")
            print("=" * 80)
            print(f"Converged after {self.iterations:,} iterations")
            if self.variant == 'imp':
                print(f"Stagnation at termination: "
                      f"{self.iters_since_best_improvement:,} iters since last best "
                      f"(limit: {self._stagnation_limit():,})")
            else:
                print(f"Idle at termination: {self.idle_iterations:,} "
                      f"(1% threshold: {0.01 * self.iterations:.0f})")
            print(f"Variant:         {self.variant}")
            print(f"Bound updates:   {self.bound_updates}")
            print(f"Initial penalty: {self.penalty_history[0]}")
            print(f"Final penalty:   {self.best_penalty}")
            print(
                f"Improvement:     "
                f"{self.penalty_history[0] - self.best_penalty} "
                f"({(self.penalty_history[0] - self.best_penalty) / self.penalty_history[0] * 100:.1f}%)"
            )
            if self.variant == 'imp':
                print(f"Improving moves: {self.improving_moves:,} "
                      f"({self.improving_moves / self.iterations * 100:.1f}% of iters)")
            print(f"Accepted moves:  {self.accepted_moves:,}")
            print(f"Rejected moves:  {self.rejected_moves:,}")
            print(f"Total time:      {elapsed_time:.2f}s")
            print()

        return best_solution, {
            'initial_penalty':     self.penalty_history[0],
            'final_penalty':       self.best_penalty,
            'improvement':         self.penalty_history[0] - self.best_penalty,
            'improvement_percent': (
                (self.penalty_history[0] - self.best_penalty)
                / self.penalty_history[0] * 100
            ),
            'iterations':          self.iterations,
            'improving_moves':     self.improving_moves,
            'accepted_moves':      self.accepted_moves,
            'rejected_moves':      self.rejected_moves,
            'bound_updates':       self.bound_updates,
            'elapsed_time':        elapsed_time,
            'penalty_history':     self.penalty_history,
            'operator_statistics': self.operator_statistics,
            'Lc':                  self.Lc,
            'variant':             self.variant,
        }

    def print_operator_statistics(self):
        operator_names = [
            "Swap Shifts (Same Day)",
            "Swap All Shifts (Two Days)",
            "Cyclic Swap",
            "Move Pattern",
            "Swap Pattern",
            "Three-Nurse Rotation"
        ]
        print("=" * 80)
        print("OPERATOR STATISTICS")
        print("=" * 80)
        print(f"{'Operator':<30} {'Attempts':>10} {'Accepted':>10} {'Rate':>10}")
        print("-" * 80)
        for idx in range(len(self.operators)):
            name     = (operator_names[idx]
                        if idx < len(operator_names)
                        else f"Operator {idx}")
            s        = self.operator_statistics[idx]
            attempts = s['attempts']
            accepted = s['accepted']
            rate     = (accepted / attempts * 100) if attempts > 0 else 0.0
            print(f"{name:<30} {attempts:>10} {accepted:>10} {rate:>9.1f}%")
        print("=" * 80)


# Convenience aliases
SCHC_all = lambda *args, **kwargs: SCHC(*args, variant='all', **kwargs)
SCHC_acp = lambda *args, **kwargs: SCHC(*args, variant='acp', **kwargs)
SCHC_imp = lambda *args, **kwargs: SCHC(*args, variant='imp', **kwargs)