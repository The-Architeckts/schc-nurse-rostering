'''
Neighborhood operators for Hill Climbing and SCHC.
Each operator generates a neighbor solution by modifying the current solution.
'''

import random
from solution import Solution
from models import ShiftType
from constraints import check_coverage_violations, check_single_assignment_violations


def get_all_operators():
    '''
    Returns list of all available operator functions.
    Used for testing and random operator selection in HC/SCHC.
    
    Note: Operators 1 (Single Shift Change) and 4 (Change Shift Type) 
    have been removed because they break coverage constraints in tight schedules.
    '''
    return [
        operator_swap_shifts_same_day,           # Operator 2
        operator_swap_shifts_same_nurse,         # Operator 3
        operator_swap_all_shifts_two_days,       # Operator 5
        operator_cyclic_swap,                     # Operator 6
        operator_move_pattern,                    # Operator 7
        operator_swap_pattern,                    # Operator 8
        operator_three_nurse_rotation             # Operator 9
    ]


# ============================================================================
# OPERATOR 2: SWAP SHIFTS (SAME DAY)
# ============================================================================

def operator_swap_shifts_same_day(solution, instance_data):
    '''
    Swap shift assignments between two nurses on the same day.
    
    This is coverage-preserving: if both nurses were working, they still work
    (just different shifts). Useful for improving nurse preferences without
    breaking coverage.
    
    Example:
        Day 5: Nurse 1 (E) ↔ Nurse 3 (L)
        Result: Nurse 1 now works L, Nurse 3 now works E
    
    Args:
        solution: Current Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        new_solution: Modified Solution object (or None if no valid move found)
    '''
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    for _ in range(50):
        day = random.randint(0, n_days - 1)
        nurse1 = random.randint(0, n_nurses - 1)
        nurse2 = random.randint(0, n_nurses - 1)
        
        if nurse1 == nurse2:
            continue
        
        # Get current shifts
        shift1 = solution.schedule[nurse1][day]
        shift2 = solution.schedule[nurse2][day]
        
        # Create new solution with swapped shifts
        new_solution = solution.copy()
        new_solution.assign_shift(nurse1, day, shift2)
        new_solution.assign_shift(nurse2, day, shift1)
        
        if is_feasible(new_solution, instance_data):
            return new_solution
    
    return None


# ============================================================================
# OPERATOR 3: SWAP SHIFTS (SAME NURSE, DIFFERENT DAYS)
# ============================================================================

def operator_swap_shifts_same_nurse(solution, instance_data):
    '''
    Swap shift assignments for one nurse across two different days.
    
    This can help improve series constraints (consecutive work patterns)
    without affecting other nurses.
    
    Example:
        Nurse 2: Day 3 (E) ↔ Day 7 (OFF)
        Result: Nurse 2 now OFF on day 3, works E on day 7
    
    Args:
        solution: Current Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        new_solution: Modified Solution object (or None if no valid move found)
    '''
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    for _ in range(50):
        nurse_id = random.randint(0, n_nurses - 1)
        day1 = random.randint(0, n_days - 1)
        day2 = random.randint(0, n_days - 1)
        
        if day1 == day2:
            continue
        
        # Get current shifts
        shift1 = solution.schedule[nurse_id][day1]
        shift2 = solution.schedule[nurse_id][day2]
        
        # Create new solution with swapped shifts
        new_solution = solution.copy()
        new_solution.assign_shift(nurse_id, day1, shift2)
        new_solution.assign_shift(nurse_id, day2, shift1)
        
        if is_feasible(new_solution, instance_data):
            return new_solution
    
    return None


# ============================================================================
# OPERATOR 5: SWAP ALL SHIFTS (TWO DAYS, TWO NURSES)
# ============================================================================

def operator_swap_all_shifts_two_days(solution, instance_data):
    '''
    Exchange shifts between two nurses on two different days.
    
    This creates a 2x2 swap pattern. Can help redistribute workload
    and improve schedule quality for both nurses simultaneously.
    
    Example:
        Nurse 1: Day 3 (E), Day 7 (L)
        Nurse 2: Day 3 (OFF), Day 7 (D)
        
        After swap:
        Nurse 1: Day 3 (OFF), Day 7 (D)
        Nurse 2: Day 3 (E), Day 7 (L)
    
    Args:
        solution: Current Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        new_solution: Modified Solution object (or None if no valid move found)
    '''
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    for _ in range(50):
        nurse1 = random.randint(0, n_nurses - 1)
        nurse2 = random.randint(0, n_nurses - 1)
        day1 = random.randint(0, n_days - 1)
        day2 = random.randint(0, n_days - 1)
        
        if nurse1 == nurse2 or day1 == day2:
            continue
        
        # Get all four shifts
        n1_d1 = solution.schedule[nurse1][day1]
        n1_d2 = solution.schedule[nurse1][day2]
        n2_d1 = solution.schedule[nurse2][day1]
        n2_d2 = solution.schedule[nurse2][day2]
        
        # Swap: nurse1 gets nurse2's shifts, nurse2 gets nurse1's shifts
        new_solution = solution.copy()
        new_solution.assign_shift(nurse1, day1, n2_d1)
        new_solution.assign_shift(nurse1, day2, n2_d2)
        new_solution.assign_shift(nurse2, day1, n1_d1)
        new_solution.assign_shift(nurse2, day2, n1_d2)
        
        if is_feasible(new_solution, instance_data):
            return new_solution
    
    return None


# ============================================================================
# OPERATOR 6: CYCLIC SWAP (4-WAY ROTATION)
# ============================================================================

def operator_cyclic_swap(solution, instance_data):
    '''
    Perform a 4-way cyclic rotation of shifts between 2 nurses on 2 days.
    
    This is more complex than a simple swap - shifts rotate in a cycle.
    
    Example:
        Nurse 1, Day 3: E
        Nurse 1, Day 7: L
        Nurse 2, Day 3: D
        Nurse 2, Day 7: OFF
        
        After cyclic swap (clockwise):
        Nurse 1, Day 3: OFF  (from Nurse 2, Day 7)
        Nurse 1, Day 7: E    (from Nurse 1, Day 3)
        Nurse 2, Day 3: L    (from Nurse 1, Day 7)
        Nurse 2, Day 7: D    (from Nurse 2, Day 3)
    
    Args:
        solution: Current Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        new_solution: Modified Solution object (or None if no valid move found)
    '''
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    for _ in range(50):
        nurse1 = random.randint(0, n_nurses - 1)
        nurse2 = random.randint(0, n_nurses - 1)
        day1 = random.randint(0, n_days - 1)
        day2 = random.randint(0, n_days - 1)
        
        if nurse1 == nurse2 or day1 == day2:
            continue
        
        # Get all four shifts
        n1_d1 = solution.schedule[nurse1][day1]
        n1_d2 = solution.schedule[nurse1][day2]
        n2_d1 = solution.schedule[nurse2][day1]
        n2_d2 = solution.schedule[nurse2][day2]
        
        # Cyclic rotation: n1_d1 → n1_d2 → n2_d2 → n2_d1 → n1_d1
        new_solution = solution.copy()
        new_solution.assign_shift(nurse1, day2, n1_d1)  # n1_d1 → n1_d2
        new_solution.assign_shift(nurse2, day2, n1_d2)  # n1_d2 → n2_d2
        new_solution.assign_shift(nurse2, day1, n2_d2)  # n2_d2 → n2_d1
        new_solution.assign_shift(nurse1, day1, n2_d1)  # n2_d1 → n1_d1
        
        if is_feasible(new_solution, instance_data):
            return new_solution
    
    return None


# ============================================================================
# OPERATOR 7: MOVE PATTERN (2-3 CONSECUTIVE SHIFTS)
# ============================================================================

def operator_move_pattern(solution, instance_data):
    '''
    Move a sequence of 2-3 consecutive shifts from one nurse to another.
    
    This can help create better consecutive work patterns and redistribute
    workload in larger chunks.
    
    Example:
        Nurse 1: Days 5-7: E, L, D
        Nurse 3: Days 5-7: OFF, OFF, OFF
        
        After move:
        Nurse 1: Days 5-7: OFF, OFF, OFF
        Nurse 3: Days 5-7: E, L, D
    
    Args:
        solution: Current Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        new_solution: Modified Solution object (or None if no valid move found)
    '''
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    for _ in range(50):
        nurse_from = random.randint(0, n_nurses - 1)
        nurse_to = random.randint(0, n_nurses - 1)
        
        if nurse_from == nurse_to:
            continue
        
        # Random pattern length (2 or 3 days)
        pattern_length = random.randint(2, 3)
        
        # Random starting day (ensure pattern fits in schedule)
        if n_days - pattern_length < 0:
            continue
        start_day = random.randint(0, n_days - pattern_length)
        
        # Create new solution
        new_solution = solution.copy()
        
        # Move pattern: nurse_from shifts → nurse_to, nurse_from gets OFF
        for offset in range(pattern_length):
            day = start_day + offset
            shift = solution.schedule[nurse_from][day]
            new_solution.assign_shift(nurse_to, day, shift)
            new_solution.assign_shift(nurse_from, day, ShiftType.OFF)
        
        if is_feasible(new_solution, instance_data):
            return new_solution
    
    return None


# ============================================================================
# OPERATOR 8: SWAP PATTERN (2-3 CONSECUTIVE SHIFTS)
# ============================================================================

def operator_swap_pattern(solution, instance_data):
    '''
    Exchange sequences of 2-3 consecutive shifts between two nurses.
    
    Similar to move_pattern, but swaps instead of just moving.
    Both nurses get new patterns.
    
    Example:
        Nurse 1: Days 5-7: E, L, D
        Nurse 3: Days 5-7: OFF, N, N
        
        After swap:
        Nurse 1: Days 5-7: OFF, N, N
        Nurse 3: Days 5-7: E, L, D
    
    Args:
        solution: Current Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        new_solution: Modified Solution object (or None if no valid move found)
    '''
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    for _ in range(50):
        nurse1 = random.randint(0, n_nurses - 1)
        nurse2 = random.randint(0, n_nurses - 1)
        
        if nurse1 == nurse2:
            continue
        
        # Random pattern length (2 or 3 days)
        pattern_length = random.randint(2, 3)
        
        # Random starting day
        if n_days - pattern_length < 0:
            continue
        start_day = random.randint(0, n_days - pattern_length)
        
        # Create new solution
        new_solution = solution.copy()
        
        # Swap patterns
        for offset in range(pattern_length):
            day = start_day + offset
            shift1 = solution.schedule[nurse1][day]
            shift2 = solution.schedule[nurse2][day]
            new_solution.assign_shift(nurse1, day, shift2)
            new_solution.assign_shift(nurse2, day, shift1)
        
        if is_feasible(new_solution, instance_data):
            return new_solution
    
    return None


# ============================================================================
# OPERATOR 9: THREE-NURSE ROTATION (SAME DAY)
# ============================================================================

def operator_three_nurse_rotation(solution, instance_data):
    '''
    Rotate shift assignments among three nurses on the same day.
    
    This creates more complex swap patterns that can escape local optima
    better than 2-nurse swaps.
    
    Example:
        Day 5:
        Nurse 1: E
        Nurse 2: L
        Nurse 3: D
        
        After rotation (clockwise):
        Nurse 1: D (from Nurse 3)
        Nurse 2: E (from Nurse 1)
        Nurse 3: L (from Nurse 2)
    
    Args:
        solution: Current Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        new_solution: Modified Solution object (or None if no valid move found)
    '''
    n_nurses = len(instance_data['nurses'])
    n_days = instance_data['period']
    
    if n_nurses < 3:
        return None  # Need at least 3 nurses
    
    for _ in range(50):
        day = random.randint(0, n_days - 1)
        
        # Select 3 different nurses
        nurses = random.sample(range(n_nurses), 3)
        n1, n2, n3 = nurses[0], nurses[1], nurses[2]
        
        # Get current shifts
        shift1 = solution.schedule[n1][day]
        shift2 = solution.schedule[n2][day]
        shift3 = solution.schedule[n3][day]
        
        # Rotate: n1 → n2 → n3 → n1
        new_solution = solution.copy()
        new_solution.assign_shift(n2, day, shift1)  # n1's shift → n2
        new_solution.assign_shift(n3, day, shift2)  # n2's shift → n3
        new_solution.assign_shift(n1, day, shift3)  # n3's shift → n1
        
        if is_feasible(new_solution, instance_data):
            return new_solution
    
    return None


# ============================================================================
# HELPER: FEASIBILITY CHECKING
# ============================================================================

def is_feasible(solution, instance_data):
    '''
    Check if a solution satisfies all hard constraints.
    
    Hard constraints:
    1. All coverage requirements met (each shift has required nurses)
    2. Single assignment per day (each nurse works ≤1 shift per day)
    
    Args:
        solution: Solution object to check
        instance_data: Dict from load_instance()
    
    Returns:
        bool: True if feasible, False otherwise
    '''
    coverage_violations = check_coverage_violations(solution, instance_data)
    single_violations = check_single_assignment_violations(solution)
    
    return (coverage_violations == 0 and single_violations == 0)