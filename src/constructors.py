'''
Constructors for generating initial solutions.
'''

from solution import Solution
from models import ShiftType

def greedy_constructor(instance_data):
    '''
    Create a baseline feasible solution using round-robin greedy assignment.
    
    Strategy:
    - Iterate through all coverage requirements
    - For each requirement, assign nurses round-robin
    - Goal: Satisfy hard constraints (coverage)
    '''
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    solution = Solution(n_nurses, n_days)
    
    # Sort coverage requirements by day, then by shift
    # (to process them in chronological order)
    coverage_reqs = sorted(instance_data['coverage'], 
                          key=lambda x: (x['dayIndex'], x['shiftTypeIds'][0]))
    
    # Process each coverage requirement
    for idx, req in enumerate(coverage_reqs):
        day = req['dayIndex']
        shift_str = req['shiftTypeIds'][0]  # 'E', 'L', 'D', or 'N'
        shift_type = ShiftType.from_string(shift_str)
        needed = req['min']  # How many nurses needed
        
        assigned_count = 0
        
        # Round-robin: start from different nurse each time
        start_nurse = idx % n_nurses
        
        for i in range(n_nurses):
            if assigned_count >= needed:
                break  # We've assigned enough nurses
            
            nurse_id = (start_nurse + i) % n_nurses
            
            # Check if nurse is available (not already working this day)
            current_assignment = solution.get_assignment(nurse_id, day)
            
            if current_assignment == ShiftType.OFF:
                # Nurse is free - assign them!
                solution.assign_shift(nurse_id, day, shift_type)
                assigned_count += 1
        
        # TODO: What if we couldn't assign enough nurses?
        # For now, we'll just continue (might create hard constraint violation)
    
    return solution