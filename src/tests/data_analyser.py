'''
Temporary test file - used to verify that components work.
'''

import sys
from pathlib import Path

# Add parent directory to path so we can import from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import load_instance
from constructors import greedy_constructor
from models import ShiftType
from constraints import evaluate_solution, _identify_weekends

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

'''print("\n" + "-"*80)
print("INDIVIDUAL NURSE PENALTIES:")
print("-"*80)

for nurse_id in range(len(instance['nurses'])):
    nurse = instance['nurses'][nurse_id]
    contract = instance['contracts'][nurse.contract_id]
    nurse_schedule = solution.schedule[nurse_id]
    
    from constraints import _check_counter_constraints
    nurse_penalty = _check_counter_constraints(contract, nurse_schedule)
    
    days_worked = sum(1 for day in nurse_schedule if day != ShiftType.OFF)
    
    print(f"Nurse {nurse_id} (Contract {nurse.contract_id}): {days_worked} days, penalty = {nurse_penalty}")'''

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

# ============================================================================
# COMPLETE CONSTRAINT BREAKDOWN (ALL 7 TYPES)
# ============================================================================
print("\n" + "="*80)
print("COMPLETE PENALTY BREAKDOWN BY CONSTRAINT TYPE")
print("="*80)

from constraints import (
    _check_counter_constraints,
    _check_series_constraints, 
    _check_pattern_constraints,
    _check_complete_weekends,
    _check_identical_weekends,
    _check_shift_off_requests,
    _check_time_off_requests
)

total_counter = 0
total_series = 0
total_pattern = 0
total_complete_weekend = 0
total_identical_weekend = 0
total_shift_off = 0
total_time_off = 0

print("\n" + "-"*80)
print("FIRST 3 NURSES DETAILED BREAKDOWN:")
print("-"*80)

for nurse_id in range(min(3, len(instance['nurses']))):
    nurse = instance['nurses'][nurse_id]
    contract = instance['contracts'][nurse.contract_id]
    nurse_schedule = solution.schedule[nurse_id]
    
    counter_penalty = _check_counter_constraints(contract, nurse_schedule)
    series_penalty = _check_series_constraints(contract, nurse_schedule)
    pattern_penalty = _check_pattern_constraints(contract, nurse_schedule)
    complete_weekend_penalty = _check_complete_weekends(nurse, nurse_schedule, instance)
    identical_weekend_penalty = _check_identical_weekends(nurse, nurse_schedule, instance)
    shift_off_penalty = _check_shift_off_requests(nurse, nurse_schedule)
    time_off_penalty = _check_time_off_requests(nurse, nurse_schedule)
    
    total = (counter_penalty + series_penalty + pattern_penalty + 
             complete_weekend_penalty + identical_weekend_penalty +
             shift_off_penalty + time_off_penalty)
    
    print(f"\nNurse {nurse_id} (Contract {nurse.contract_id}):")
    print(f"  Counter:             {counter_penalty}")
    print(f"  Series:              {series_penalty}")
    print(f"  Pattern:             {pattern_penalty}")
    print(f"  Complete Weekends:   {complete_weekend_penalty}")
    print(f"  Identical Weekends:  {identical_weekend_penalty}")
    print(f"  Shift-Off Requests:  {shift_off_penalty}")
    print(f"  Time-Off Requests:   {time_off_penalty}")
    print(f"  TOTAL:               {total}")

print("\n" + "-"*80)
print("ALL NURSES TOTALS:")
print("-"*80)

for nurse_id in range(len(instance['nurses'])):
    nurse = instance['nurses'][nurse_id]
    contract = instance['contracts'][nurse.contract_id]
    nurse_schedule = solution.schedule[nurse_id]
    
    total_counter += _check_counter_constraints(contract, nurse_schedule)
    total_series += _check_series_constraints(contract, nurse_schedule)
    total_pattern += _check_pattern_constraints(contract, nurse_schedule)
    total_complete_weekend += _check_complete_weekends(nurse, nurse_schedule, instance)
    total_identical_weekend += _check_identical_weekends(nurse, nurse_schedule, instance)
    total_shift_off += _check_shift_off_requests(nurse, nurse_schedule)
    total_time_off += _check_time_off_requests(nurse, nurse_schedule)

print(f"Counter Constraints:        {total_counter}")
print(f"Series Constraints:         {total_series}")
print(f"Pattern Constraints:        {total_pattern}")
print(f"Complete Weekend:           {total_complete_weekend}")
print(f"Identical Weekend:          {total_identical_weekend}")
print(f"Shift-Off Requests:         {total_shift_off}")
print(f"Time-Off Requests:          {total_time_off}")
print(f"{'-'*80}")
print(f"GRAND TOTAL:                {total_counter + total_series + total_pattern + total_complete_weekend + total_identical_weekend + total_shift_off + total_time_off}")
print(f"Expected (from evaluate):   {penalty}")

# ============================================================================
# WEEKEND DETECTION VERIFICATION
# ============================================================================
print("\n" + "="*80)
print("WEEKEND DETECTION VERIFICATION")
print("="*80)

from constraints import _identify_weekends

# Show weekend structure
weekend_comp = instance['weekend_compositions']['0']
print(f"\nWeekend Composition: {weekend_comp['startDay']} to {weekend_comp['endDay']}")
print(f"Planning period starts: {instance['start_day']}")
print(f"Planning horizon: {instance['period']} days")

weekends = _identify_weekends(instance['period'], instance['start_day'], weekend_comp)
print(f"\nIdentified {len(weekends)} weekends:")
for i, weekend_days in enumerate(weekends):
    print(f"  Weekend {i+1}: Days {weekend_days}")

# Show first nurse's weekend schedule
print(f"\n" + "-"*80)
print("FIRST NURSE'S WEEKEND SCHEDULE:")
print("-"*80)

nurse = instance['nurses'][0]
nurse_schedule = solution.schedule[0]

for i, weekend_days in enumerate(weekends):
    weekend_shifts = [ShiftType.to_string(nurse_schedule[day]) for day in weekend_days]
    works_any = any(nurse_schedule[day] != ShiftType.OFF for day in weekend_days)
    works_all = all(nurse_schedule[day] != ShiftType.OFF for day in weekend_days)
    
    print(f"\nWeekend {i+1} (Days {weekend_days}):")
    print(f"  Shifts: {weekend_shifts}")
    print(f"  Works any day? {works_any}")
    print(f"  Works all days? {works_all}")
    
    if works_any and not works_all:
        print(f"  ❌ VIOLATES complete weekend constraint")
    elif works_any:
        # Check identical shifts
        working_shifts = [nurse_schedule[day] for day in weekend_days 
                         if nurse_schedule[day] != ShiftType.OFF]
        if len(set(working_shifts)) > 1:
            print(f"  ❌ VIOLATES identical weekend constraint (different shifts)")
        else:
            print(f"  ✓ OK (same shift on all working days)")

# ============================================================================
# REQUEST VIOLATIONS DETAIL
# ============================================================================
print("\n" + "="*80)
print("REQUEST VIOLATIONS DETAIL (FIRST 3 NURSES)")
print("="*80)

for nurse_id in range(min(3, len(instance['nurses']))):
    nurse = instance['nurses'][nurse_id]
    nurse_schedule = solution.schedule[nurse_id]
    
    print(f"\n--- Nurse {nurse_id} ---")
    
    # Shift-off requests
    print(f"\nShift-Off Requests ({len(nurse.shift_off_requests)} total):")
    violations = 0
    for req in nurse.shift_off_requests:
        day = req['dayIndex']
        requested_off = req['shiftTypeId']
        actual_shift = ShiftType.to_string(nurse_schedule[day])
        shift_value = ShiftType.from_string(requested_off)
        
        if nurse_schedule[day] == shift_value:
            print(f"  Day {day}: Requested OFF from {requested_off}, but assigned {actual_shift} ❌")
            violations += 1
        else:
            print(f"  Day {day}: Requested OFF from {requested_off}, assigned {actual_shift} ✓")
    
    if violations == 0:
        print(f"  ✓ All shift-off requests honored")
    
    # Time-off requests
    print(f"\nTime-Off Requests ({len(nurse.time_off_requests)} total):")
    violations = 0
    for req in nurse.time_off_requests:
        day = req['dayIndex']
        actual_shift = ShiftType.to_string(nurse_schedule[day])
        
        if nurse_schedule[day] != ShiftType.OFF:
            print(f"  Day {day}: Requested complete day OFF, but assigned {actual_shift} ❌")
            violations += 1
        else:
            print(f"  Day {day}: Requested complete day OFF, honored ✓")
    
    if violations == 0:
        print(f"  ✓ All time-off requests honored")

print("\n" + "="*80)