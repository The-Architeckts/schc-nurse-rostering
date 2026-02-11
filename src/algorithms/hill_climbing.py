'''
Hill Climbing (HC) algorithm for Nurse Rostering Problem.
This is equivalent to SCHC with Lc=0 (counter limit = 0).
'''

import random
import time
import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from operators import get_all_operators
from constraints import evaluate_solution


class HillClimbing:
    '''
    Standard Hill Climbing algorithm (greedy ascent/descent).
    '''
    
    def __init__(self, instance_data, max_idle_iterations=1000, random_seed=None):
        '''
        Initialize Hill Climbing.
        
        Args:
            instance_data: Dict from load_instance()
            max_idle_iterations: Stop after this many non-improving iterations
            random_seed: For reproducibility (None = random)
        '''
        self.instance_data = instance_data
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
        self.operator_statistics = {i: {'attempts': 0, 'accepted': 0} 
                                    for i in range(len(self.operators))}
    
    
    def optimize(self, initial_solution, verbose=True):
        '''
        Run Hill Climbing optimization.
        
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
        
        self.penalty_history.append(current_penalty)
        
        if verbose:
            print("="*80)
            print("HILL CLIMBING OPTIMIZATION")
            print("="*80)
            print(f"Initial penalty: {current_penalty}")
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
            
            # If operator failed to generate valid neighbor, try again
            if neighbor is None:
                continue
            
            # Evaluate neighbor
            neighbor_penalty = evaluate_solution(neighbor, self.instance_data)
            
            # Accept only if strictly better (greedy HC)
            if neighbor_penalty < current_penalty:
                # ACCEPT - found improvement
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
                        print(f"Iter {self.iterations:5d} | "
                              f"Penalty: {current_penalty:3d} | "
                              f"Improvement: {improvement:+3d} | "
                              f"Time: {elapsed:.1f}s")
            else:
                # REJECT - no improvement
                self.rejected_moves += 1
                self.idle_iterations += 1
            
            # Record penalty history (sample every 10 iterations to save memory)
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
            'elapsed_time': elapsed_time,
            'penalty_history': self.penalty_history,
            'operator_statistics': self.operator_statistics
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
        
        for idx, name in enumerate(operator_names):
            stats = self.operator_statistics[idx]
            attempts = stats['attempts']
            accepted = stats['accepted']
            rate = (accepted / attempts * 100) if attempts > 0 else 0.0
            
            print(f"{name:<30} {attempts:>10} {accepted:>10} {rate:>9.1f}%")
        
        print("="*80)


class SteepestDescentHC(HillClimbing):
    '''
    Steepest Descent Hill Climbing variant.
    Evaluates ALL operators and selects the best improvement.
    Slower but potentially finds better solutions.
    '''
    
    def optimize(self, initial_solution, verbose=True):
        '''
        Run Steepest Descent Hill Climbing.
        
        At each iteration, tries all operators and accepts the best one.
        '''
        start_time = time.time()
        
        # Initialize
        current_solution = initial_solution.copy()
        current_penalty = evaluate_solution(current_solution, self.instance_data)
        
        best_solution = current_solution.copy()
        self.best_penalty = current_penalty
        self.penalty_history.append(current_penalty)
        
        if verbose:
            print("="*80)
            print("STEEPEST DESCENT HILL CLIMBING")
            print("="*80)
            print(f"Initial penalty: {current_penalty}")
            print(f"Max idle iterations: {self.max_idle_iterations}")
            print(f"Available operators: {len(self.operators)}")
            print()
        
        # Main optimization loop
        while self.idle_iterations < self.max_idle_iterations:
            self.iterations += 1
            
            # Try ALL operators and find best improvement
            best_neighbor = None
            best_neighbor_penalty = current_penalty
            best_operator_idx = -1
            
            for operator_idx, operator in enumerate(self.operators):
                self.operator_statistics[operator_idx]['attempts'] += 1
                
                # Generate neighbor
                neighbor = operator(current_solution, self.instance_data)
                
                if neighbor is None:
                    continue
                
                # Evaluate neighbor
                neighbor_penalty = evaluate_solution(neighbor, self.instance_data)
                
                # Track best improvement
                if neighbor_penalty < best_neighbor_penalty:
                    best_neighbor = neighbor
                    best_neighbor_penalty = neighbor_penalty
                    best_operator_idx = operator_idx
            
            # Accept best neighbor if it improves
            if best_neighbor is not None and best_neighbor_penalty < current_penalty:
                current_solution = best_neighbor
                current_penalty = best_neighbor_penalty
                self.accepted_moves += 1
                self.operator_statistics[best_operator_idx]['accepted'] += 1
                self.idle_iterations = 0
                
                # Update best solution
                if best_neighbor_penalty < self.best_penalty:
                    best_solution = best_neighbor.copy()
                    self.best_penalty = best_neighbor_penalty
                    
                    if verbose and self.iterations % 10 == 0:
                        elapsed = time.time() - start_time
                        improvement = self.penalty_history[0] - current_penalty
                        print(f"Iter {self.iterations:5d} | "
                              f"Penalty: {current_penalty:3d} | "
                              f"Improvement: {improvement:+3d} | "
                              f"Time: {elapsed:.1f}s")
            else:
                self.rejected_moves += 1
                self.idle_iterations += 1
            
            # Record penalty history
            if self.iterations % 10 == 0:
                self.penalty_history.append(current_penalty)
        
        # Complete
        elapsed_time = time.time() - start_time
        
        if verbose:
            print()
            print("="*80)
            print("OPTIMIZATION COMPLETE")
            print("="*80)
            print(f"Converged after {self.iterations} iterations")
            print(f"Initial penalty: {self.penalty_history[0]}")
            print(f"Final penalty:   {self.best_penalty}")
            print(f"Improvement:     {self.penalty_history[0] - self.best_penalty} "
                  f"({(self.penalty_history[0] - self.best_penalty) / self.penalty_history[0] * 100:.1f}%)")
            print(f"Total time:      {elapsed_time:.2f}s")
            print()
        
        stats = {
            'initial_penalty': self.penalty_history[0],
            'final_penalty': self.best_penalty,
            'improvement': self.penalty_history[0] - self.best_penalty,
            'improvement_percent': (self.penalty_history[0] - self.best_penalty) / self.penalty_history[0] * 100,
            'iterations': self.iterations,
            'accepted_moves': self.accepted_moves,
            'rejected_moves': self.rejected_moves,
            'elapsed_time': elapsed_time,
            'penalty_history': self.penalty_history,
            'operator_statistics': self.operator_statistics
        }
        
        return best_solution, stats