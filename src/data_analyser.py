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