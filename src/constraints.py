"""
Constraint evaluation for Nurse Rostering Problem.
Calculates penalty = (hard_violations × 10^6) + soft_violations
"""

def evaluate_solution(solution, instance_data):
    """
    Calculate total penalty for a solution.
    
    Args:
        solution: Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        total_penalty: int
    """
    penalty = 0
    
    # Check each nurse's schedule against their contract
    for nurse_id, nurse in enumerate(instance_data['nurses']):
        contract = instance_data['contracts'][nurse.contract_id]
        nurse_schedule = solution.schedule[nurse_id]
        
        # Check counter constraints (days worked, etc.)
        penalty += _check_counter_constraints(contract, nurse_schedule)

        penalty += _check_series_constraints(contract, nurse_schedule)

        penalty += _check_pattern_constraints(contract, nurse_schedule)
        # TODO: Add more constraint types here
        # penalty += _check_series_constraints(contract, nurse_schedule)
        # penalty += _check_pattern_constraints(contract, nurse_schedule)
    
    # TODO: Check hard constraints (coverage, single assignment per day)
    # penalty += 10**6 * check_coverage_violations(solution, instance_data)
    
    return penalty


def _check_counter_constraints(contract, schedule):
    """Check counter constraints (total days worked, etc.)"""
    penalty = 0
    
    for constraint in contract.counterConstraints:
        if constraint['variant'] == 'daysWorked':
            # Count working days
            total_days = sum(1 for day in schedule if day != 1)  # 1 = OFF
            
            min_days = constraint['min']
            max_days = constraint['max']
            
            # Calculate penalty
            if total_days < min_days:
                penalty += (min_days - total_days)
            elif total_days > max_days:
                penalty += (total_days - max_days)
    
    return penalty

def _check_series_constraints(contract, schedule):
    """Check series constraints (consecutive working/idle days)"""
    penalty = 0
    for constraint in contract.seriesConstraints:
        variant = constraint['variant']      # 'daysWorked' or 'daysIdle'
        min_length = constraint['min']
        max_length = constraint['max']
        
        # Extract all consecutive series from schedule
        series_list = _extract_series(schedule, variant)
        
        # Penalize each series that violates min/max
        for series_length in series_list:
            if series_length < min_length:
                penalty += (min_length - series_length)
            elif series_length > max_length:
                penalty += (series_length - max_length)
    
    return penalty

def _extract_series(schedule, variant):
    '''Extract consecutive series from a schedule.'''
    series_list = []
    current_length = 0
    
    for shift in schedule:
        is_working = (shift != 1)  # 1 = OFF, anything else = working
        
        # Are we counting this type of day?
        if (variant == 'daysWorked' and is_working) or \
           (variant == 'daysIdle' and not is_working):
            current_length += 1
        else:
            # Series ended - record it if length > 0
            if current_length > 0:
                series_list.append(current_length)
            current_length = 0
    
    # Record final series if schedule ends with one
    if current_length > 0:
        series_list.append(current_length)
    
    return series_list

def _check_pattern_constraints(contract, schedule):
    '''Check pattern constraints (forbidden shift sequences).'''
    from models import ShiftType
    
    penalty = 0
    
    for pattern in contract.patternConstraints:
        entries = pattern['entries']
        pattern_length = len(entries)
        
        # Convert pattern from strings to shift values
        # entries = [{'shiftTypes': ['L']}, {'shiftTypes': ['D']}]
        # → pattern_shifts = [[8], [4]]  (L=8, D=4)
        pattern_shifts = []
        for entry in entries:
            shift_types = entry['shiftTypeIds']['shiftTypes']
            shift_values = [ShiftType.from_string(st) for st in shift_types]
            pattern_shifts.append(shift_values)
        
        # Scan through schedule looking for this pattern
        for i in range(len(schedule) - pattern_length + 1):
            match = True
            for j in range(pattern_length):
                # Does schedule[i+j] match pattern_shifts[j]?
                if schedule[i + j] not in pattern_shifts[j]:
                    match = False
                    break
            
            if match:
                penalty += 1  # Found forbidden pattern
    
    return penalty