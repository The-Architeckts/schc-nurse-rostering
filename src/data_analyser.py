"""
Temporary test file - used to verify that components work.
"""

from data_loader import load_instance
from solution import Solution
from models import ShiftType
from constraints import evaluate_solution
from constructors import greedy_constructor

# Load instance
instance = load_instance('data/inrc1/INRC1_sprint01.json')

print(f"Loaded: {instance['name']}")
print(f"Nurses: {len(instance['nurses'])}")
print(f"Days: {instance['period']}")

# Generate baseline solution
print("\n" + "="*80)
print("GENERATING BASELINE SOLUTION")
print("="*80)

solution = greedy_constructor(instance)

print("\nGenerated schedule:")
solution.print_schedule()

# Evaluate it
penalty = evaluate_solution(solution, instance)
print(f"\n" + "="*80)
print(f"BASELINE SOLUTION PENALTY: {penalty}")
print("="*80)

# Check balance of the workload
print("\nWorkload distribution:")
for nurse_id in range(len(instance['nurses'])):
    schedule = solution.schedule[nurse_id]
    days_worked = sum(1 for day in schedule if day != ShiftType.OFF)
    print(f"  Nurse {nurse_id}: {days_worked} days")

print("\n" + "="*80)
print("PENALTY BREAKDOWN BY NURSE")
print("="*80)

# First, show ALL counter constraints for each unique contract
unique_contracts = set(nurse.contract_id for nurse in instance['nurses'])
print("ALL COUNTER CONSTRAINTS BY CONTRACT:")
for contract_id in sorted(unique_contracts):
    contract = instance['contracts'][contract_id]
    print(f"\nContract {contract_id}:")
    for c in contract.counterConstraints:
        print(f"  - {c['variant']}: min={c.get('min', 'N/A')}, max={c.get('max', 'N/A')}, weight={c.get('weight', 1)}")

print("\n" + "-"*80)
print("INDIVIDUAL NURSE PENALTIES:")
print("-"*80)

for nurse_id in range(len(instance['nurses'])):
    nurse = instance['nurses'][nurse_id]
    contract = instance['contracts'][nurse.contract_id]
    nurse_schedule = solution.schedule[nurse_id]
    
    from constraints import _check_counter_constraints
    nurse_penalty = _check_counter_constraints(contract, nurse_schedule)
    
    days_worked = sum(1 for day in nurse_schedule if day != ShiftType.OFF)
    
    print(f"Nurse {nurse_id} (Contract {nurse.contract_id}): {days_worked} days, penalty = {nurse_penalty}")

# ============================================================================
# DETAILED CONSTRAINT DEBUGGING
# ============================================================================
print("\n" + "="*80)
print("DETAILED SERIES CONSTRAINT VIOLATIONS")
print("="*80)

from constraints import _extract_series

for nurse_id in range(min(3, len(instance['nurses']))):  # Show first 3 nurses
    nurse = instance['nurses'][nurse_id]
    contract = instance['contracts'][nurse.contract_id]
    nurse_schedule = solution.schedule[nurse_id]
    
    print(f"\n--- Nurse {nurse_id} (Contract {nurse.contract_id}) ---")
    
    # Show the schedule
    schedule_str = " ".join([ShiftType.to_string(s) if s != 1 else "-" for s in nurse_schedule])
    print(f"Schedule: {schedule_str}")
    
    # Check each series constraint
    for constraint in contract.seriesConstraints:
        variant = constraint['variant']
        min_length = constraint['min']
        max_length = constraint['max']
        
        series_list = _extract_series(nurse_schedule, variant)
        
        print(f"\n  {variant}: min={min_length}, max={max_length}")
        print(f"  Found series: {series_list}")
        
        # Calculate violations
        violations = 0
        violation_details = []
        for series_length in series_list:
            if series_length < min_length:
                violations += (min_length - series_length)
                violation_details.append(f"Series of {series_length} (too short, need {min_length}): penalty +{min_length - series_length}")
            elif series_length > max_length:
                violations += (series_length - max_length)
                violation_details.append(f"Series of {series_length} (too long, max {max_length}): penalty +{series_length - max_length}")
        
        if violations > 0:
            print(f"  ❌ VIOLATIONS (penalty={violations}):")
            for detail in violation_details:
                print(f"     - {detail}")
        else:
            print(f"  ✓ No violations")

print("\n" + "="*80)
print("DETAILED PATTERN CONSTRAINT VIOLATIONS")
print("="*80)

from constraints import _check_pattern_constraints
from models import ShiftType

for nurse_id in range(min(3, len(instance['nurses']))):  # Show first 3 nurses
    nurse = instance['nurses'][nurse_id]
    contract = instance['contracts'][nurse.contract_id]
    nurse_schedule = solution.schedule[nurse_id]
    
    print(f"\n--- Nurse {nurse_id} (Contract {nurse.contract_id}) ---")
    
    # Show the schedule with day indices
    schedule_str = " ".join([ShiftType.to_string(s) if s != 1 else "-" for s in nurse_schedule])
    print(f"Schedule: {schedule_str}")
    
    # Check each pattern constraint
    total_pattern_violations = 0
    for pattern in contract.patternConstraints:
        entries = pattern['entries']
        pattern_length = len(entries)
        
        # Build pattern description
        pattern_desc = " → ".join([e['shiftTypeIds']['shiftTypes'][0] for e in entries])
        print(f"\n  Forbidden pattern: {pattern_desc}")
        
        # Convert pattern entries to shift values
        pattern_shifts = []
        for entry in entries:
            shift_types = entry['shiftTypeIds']['shiftTypes']
            shift_values = [ShiftType.from_string(st) for st in shift_types]
            pattern_shifts.append(shift_values)
        
        # Find all occurrences of this pattern
        violations = []
        for i in range(len(nurse_schedule) - pattern_length + 1):
            match = True
            for j in range(pattern_length):
                if nurse_schedule[i + j] not in pattern_shifts[j]:
                    match = False
                    break
            
            if match:
                # Found a violation - record the position
                day_sequence = " → ".join([ShiftType.to_string(nurse_schedule[i + j]) for j in range(pattern_length)])
                violations.append(f"Day {i}-{i+pattern_length-1}: {day_sequence}")
                total_pattern_violations += 1
        
        if violations:
            print(f"  ❌ FOUND {len(violations)} occurrence(s):")
            for v in violations:
                print(f"     - {v}")
        else:
            print(f"  ✓ No violations")
    
    if total_pattern_violations > 0:
        print(f"\n  Total pattern penalty for Nurse {nurse_id}: {total_pattern_violations}")

print("\n" + "="*80)