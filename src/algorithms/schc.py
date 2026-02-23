'''
Step Counting Hill Climbing (SCHC) algorithm for Nurse Rostering Problem.

Based on: Burke, E. K., & Bykov, Y. (2016). 
"A Step Counting Hill Climbing Algorithm applied to University Examination Timetabling."
Journal of Scheduling, 19(4), 479-492.

SCHC extends Hill Climbing by maintaining a cost bound for Lc consecutive steps,
allowing acceptance of moves that might not improve the current solution but are
still better than the bound. This enables escape from local optima.
'''

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
import time
from operators import get_all_operators
from constraints import evaluate_solution


class SCHC_all:
    '''
    Step Counting Hill Climbing - 'all' variant.
    
    The cost bound is updated after exactly Lc steps, regardless of whether
    improvements were found. The step counter increments every iteration.
    
    Algorithm:
    1. Initialize: cost_bound = initial_cost, step_counter = 0
    2. Generate neighbor
    3. If neighbor_cost < cost_bound: accept
    4. Increment step_counter
    5. If step_counter >= Lc:
          cost_bound = current_cost
          step_counter = 0
    6. Repeat until convergence
    
    Parameters:
        Lc (counter limit): Number of steps before updating cost bound
                           Lc=0 degenerates to standard Hill Climbing
    '''
    
    def __init__(self, instance_data, Lc=100, max_idle_iterations=5000, random_seed=None):
        '''
        Initialize SCHC-all.
        
        Args:
            instance_data: Dict from load_instance()
            Lc: Counter limit (number of steps before bound update)
            max_idle_iterations: Stop after this many non-improving iterations
            random_seed: For reproducibility (None = random)
        '''
        self.instance_data = instance_data
        self.Lc = Lc  # Counter limit
        self.max_idle_iterations = max_idle_iterations
        self.operators = get_all_operators()
        
        if random_seed is not None:
            random.seed(random_seed)
        
        # Statistics
        self.iterations = 0
        self.accepted_moves = 0
        self.rejected_moves = 0
        self.idle_iterations = 0
        self.best_penalty = float('inf')
        self.penalty_history = []
        self.bound_updates = 0  # Track how many times bound was updated
        self.operator_statistics = {i: {'attempts': 0, 'accepted': 0} 
                                    for i in range(len(self.operators))}
    
    
    def optimize(self, initial_solution, verbose=True):
        '''
        Run SCHC-all optimization.
        
        Args:
            initial_solution: Starting Solution object
            verbose: Print progress information
        
        Returns:
            best_solution: Best Solution found
            stats: Dictionary of performance statistics
        '''
        start_time = time.time()
        
        # Initialize
        current_solution = initial_solution.copy()
        current_penalty = evaluate_solution(current_solution, self.instance_data)
        
        best_solution = current_solution.copy()
        self.best_penalty = current_penalty
        
        # SCHC-specific: Initialize cost bound and step counter
        cost_bound = current_penalty
        step_counter = 0
        
        self.penalty_history.append(current_penalty)
        
        if verbose:
            print("="*80)
            print("STEP COUNTING HILL CLIMBING (SCHC-all)")
            print("="*80)
            print(f"Initial penalty: {current_penalty}")
            print(f"Counter limit (Lc): {self.Lc}")
            print(f"Max idle iterations: {self.max_idle_iterations}")
            print(f"Available operators: {len(self.operators)}")
            print()
        
        # Main optimization loop
        while self.idle_iterations < self.max_idle_iterations:
            self.iterations += 1
            
            # Select random operator
            operator_idx = random.randint(0, len(self.operators) - 1)
            operator = self.operators[operator_idx]
            self.operator_statistics[operator_idx]['attempts'] += 1
            
            # Generate neighbor
            neighbor = operator(current_solution, self.instance_data)
            
            # If operator failed to generate valid neighbor, continue
            if neighbor is None:
                # Important: Still increment step counter even if operator fails
                step_counter += 1
                
                # Check if we need to update bound
                if step_counter >= self.Lc:
                    cost_bound = current_penalty
                    step_counter = 0
                    self.bound_updates += 1
                
                continue
            
            # Evaluate neighbor
            neighbor_penalty = evaluate_solution(neighbor, self.instance_data)
            
            # SCHC acceptance criterion: Accept if better than BOUND (not current)
            if neighbor_penalty < cost_bound:
                # ACCEPT
                current_solution = neighbor
                current_penalty = neighbor_penalty
                self.accepted_moves += 1
                self.operator_statistics[operator_idx]['accepted'] += 1
                self.idle_iterations = 0  # Reset idle counter
                
                # Update best solution if this is the best so far
                if neighbor_penalty < self.best_penalty:
                    best_solution = neighbor.copy()
                    self.best_penalty = neighbor_penalty
                    
                    if verbose and self.iterations % 100 == 0:
                        elapsed = time.time() - start_time
                        improvement = self.penalty_history[0] - current_penalty
                        print(f"Iter {self.iterations:6d} | "
                              f"Penalty: {current_penalty:3d} | "
                              f"Bound: {cost_bound:3d} | "
                              f"Improvement: {improvement:+3d} | "
                              f"Bounds updated: {self.bound_updates:3d} | "
                              f"Time: {elapsed:.1f}s")
            else:
                # REJECT
                self.rejected_moves += 1
                self.idle_iterations += 1
            
            # SCHC step counting mechanism
            step_counter += 1
            
            # Update bound after Lc steps
            if step_counter >= self.Lc:
                cost_bound = current_penalty
                step_counter = 0
                self.bound_updates += 1
                
                if verbose and self.iterations % 1000 == 0 and self.bound_updates > 0:
                    print(f"  [Bound updated to {cost_bound} at iteration {self.iterations}]")
            
            # Record penalty history (sample every 10 iterations)
            if self.iterations % 10 == 0:
                self.penalty_history.append(current_penalty)
        
        # Optimization complete
        elapsed_time = time.time() - start_time
        
        if verbose:
            print()
            print("="*80)
            print("OPTIMIZATION COMPLETE")
            print("="*80)
            print(f"Converged after {self.iterations} iterations")
            print(f"Bound updates: {self.bound_updates}")
            print(f"Initial penalty: {self.penalty_history[0]}")
            print(f"Final penalty:   {self.best_penalty}")
            print(f"Improvement:     {self.penalty_history[0] - self.best_penalty} "
                  f"({(self.penalty_history[0] - self.best_penalty) / self.penalty_history[0] * 100:.1f}%)")
            print(f"Accepted moves:  {self.accepted_moves}")
            print(f"Rejected moves:  {self.rejected_moves}")
            print(f"Total time:      {elapsed_time:.2f}s")
            print()
        
        # Compile statistics
        stats = {
            'initial_penalty': self.penalty_history[0],
            'final_penalty': self.best_penalty,
            'improvement': self.penalty_history[0] - self.best_penalty,
            'improvement_percent': (self.penalty_history[0] - self.best_penalty) / self.penalty_history[0] * 100,
            'iterations': self.iterations,
            'accepted_moves': self.accepted_moves,
            'rejected_moves': self.rejected_moves,
            'bound_updates': self.bound_updates,
            'elapsed_time': elapsed_time,
            'penalty_history': self.penalty_history,
            'operator_statistics': self.operator_statistics,
            'Lc': self.Lc
        }
        
        return best_solution, stats
    
    
    def print_operator_statistics(self):
        '''
        Print detailed statistics about operator performance.
        '''
        operator_names = [
            "Swap Shifts (Same Day)",
            "Swap All Shifts (Two Days)",
            "Cyclic Swap",
            "Move Pattern",
            "Swap Pattern",
            "Three-Nurse Rotation"
        ]
        
        print("="*80)
        print("OPERATOR STATISTICS")
        print("="*80)
        print(f"{'Operator':<30} {'Attempts':>10} {'Accepted':>10} {'Rate':>10}")
        print("-"*80)
        
        num_operators = len(self.operators)
        
        for idx in range(num_operators):
            name = operator_names[idx] if idx < len(operator_names) else f"Operator {idx}"
            stats = self.operator_statistics[idx]
            attempts = stats['attempts']
            accepted = stats['accepted']
            rate = (accepted / attempts * 100) if attempts > 0 else 0.0
            
            print(f"{name:<30} {attempts:>10} {accepted:>10} {rate:>9.1f}%")
        
        print("="*80)