"""
Constraint evaluation for Nurse Rostering Problem.
Calculates penalty = (hard_violations × 10^6) + soft_violations
"""

def evaluate_solution(solution, instance_data):
    '''
    Calculate total penalty for a solution.
    
    Args:
        solution: Solution object
        instance_data: Dict from load_instance()
    
    Returns:
        total_penalty: int
    '''
    # Check hard constraints first
    coverage_violations = check_coverage_violations(solution, instance_data)
    single_assignment_violations = check_single_assignment_violations(solution)
    
    hard_violations = coverage_violations + single_assignment_violations
    hard_penalty = hard_violations * (10 ** 6)
    
    # Check soft constraints
    soft_penalty = 0
    for nurse_id, nurse in enumerate(instance_data['nurses']):
        contract = instance_data['contracts'][nurse.contract_id]
        nurse_schedule = solution.schedule[nurse_id]
        
        soft_penalty += _check_counter_constraints(contract, nurse_schedule)
        soft_penalty += _check_series_constraints(contract, nurse_schedule)
        soft_penalty += _check_pattern_constraints(contract, nurse_schedule)
    
    return hard_penalty + soft_penalty


def _check_counter_constraints(contract, schedule):
    '''Check counter constraints (total days worked, etc.)'''
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
    '''Check series constraints (consecutive working/idle days)'''
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

def check_coverage_violations(solution, instance_data):
    '''Check if all coverage requirements are satisfied (H1: Hard Constraint).'''
    from models import ShiftType
    
    violations = 0
    coverage = instance_data['coverage']
    
    # For each coverage requirement
    for req in coverage:
        day_index = req['dayIndex']
        shift_type_ids = req['shiftTypeIds']  # This is an array!
        min_required = req['min']
        max_required = req['max']
        
        # In INRC-I, shiftTypeIds is always a single-element array for sprint instances
        shift_type_id = shift_type_ids[0]
        
        # Convert shift type string to binary value
        shift_value = ShiftType.from_string(shift_type_id)
        
        # Count how many nurses are assigned this shift on this day
        assigned_count = 0
        for nurse_id in range(len(solution.schedule)):
            if solution.schedule[nurse_id][day_index] == shift_value:
                assigned_count += 1
        
        # Calculate violations
        # Under-staffing: assigned < min
        if assigned_count < min_required:
            violations += (min_required - assigned_count)
        
        # Over-staffing: assigned > max
        elif assigned_count > max_required:
            violations += (assigned_count - max_required)
        
        # Note: In INRC-I sprint instances, min == max for all requirements
        # So we only need to match exactly
    
    return violations

def check_single_assignment_violations(solution):
    '''Check if any nurse is assigned multiple shifts on the same day (H2: Hard Constraint).'''

    violations = 0
    
    # Check each nurse's schedule
    for nurse_id in range(len(solution.schedule)):
        schedule = solution.schedule[nurse_id]

        # Encoding enforces each day have exactly one value, we validate by ensuring no day has an invalid value
        for day_index, shift in enumerate(schedule):
            # Valid shift values: 1 (OFF), 2 (N), 4 (D), 8 (L), 16 (E)
            valid_values = {1, 2, 4, 8, 16}
            
            if shift not in valid_values:
                violations += 1
                # This would indicate a serious bug in the solution representation
    
    return violations