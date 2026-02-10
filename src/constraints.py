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