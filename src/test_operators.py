'''
Comprehensive testing for all neighborhood operators.
Tests each operator individually and reports statistics.
'''

from data_loader import load_instance
from constructors import greedy_constructor
from operators import *
from constraints import evaluate_solution
from models import ShiftType

# Load instance
instance = load_instance('data/inrc1/INRC1_sprint01.json')
baseline = greedy_constructor(instance)
baseline_penalty = evaluate_solution(baseline, instance)

print("="*80)
print("NEIGHBORHOOD OPERATORS TESTING")
print("="*80)
print(f"Baseline penalty: {baseline_penalty}")
print(f"Instance: {instance['name']}, {len(instance['nurses'])} nurses, {instance['period']} days")
print()

# Get all operators
operators = get_all_operators()
operator_names = [
    "Swap Shifts (Same Day)",
    "Swap Shifts (Same Nurse)",
    "Swap All Shifts (Two Days)",
    "Cyclic Swap",
    "Move Pattern",
    "Swap Pattern",
    "Three-Nurse Rotation"
]

print("="*80)
print("TESTING EACH OPERATOR (100 attempts each)")
print("="*80)

for i, (operator_func, operator_name) in enumerate(zip(operators, operator_names), 1):
    print(f"\n{i}. {operator_name}")
    print("-" * 80)
    
    successful_moves = 0
    improving_moves = 0
    worsening_moves = 0
    neutral_moves = 0
    
    penalties = []
    
    # Try operator 100 times
    for attempt in range(100):
        neighbor = operator_func(baseline, instance)
        
        if neighbor is not None:
            successful_moves += 1
            neighbor_penalty = evaluate_solution(neighbor, instance)
            penalties.append(neighbor_penalty)
            
            if neighbor_penalty < baseline_penalty:
                improving_moves += 1
            elif neighbor_penalty > baseline_penalty:
                worsening_moves += 1
            else:
                neutral_moves += 1
    
    # Report statistics
    print(f"  Successful moves: {successful_moves}/100")
    print(f"  Improving moves:  {improving_moves} ({improving_moves/100*100:.1f}%)")
    print(f"  Worsening moves:  {worsening_moves} ({worsening_moves/100*100:.1f}%)")
    print(f"  Neutral moves:    {neutral_moves} ({neutral_moves/100*100:.1f}%)")
    
    if penalties:
        best_penalty = min(penalties)
        worst_penalty = max(penalties)
        avg_penalty = sum(penalties) / len(penalties)
        
        print(f"  Penalty range:    {best_penalty} to {worst_penalty}")
        print(f"  Average penalty:  {avg_penalty:.1f}")
        
        if best_penalty < baseline_penalty:
            improvement = baseline_penalty - best_penalty
            print(f"  ✅ BEST IMPROVEMENT: -{improvement} (penalty: {best_penalty})")
        else:
            print(f"  ❌ No improvements found")
    else:
        print(f"  ❌ FAILED: No valid moves generated")

print("\n" + "="*80)
print("DETAILED EXAMPLE: Single Shift Change")
print("="*80)

# Show detailed example of one operator
neighbor = operator_single_shift_change(baseline, instance)

if neighbor:
    print("\nBaseline schedule (first 3 nurses, first 10 days):")
    for nurse_id in range(min(3, len(instance['nurses']))):
        schedule_str = " ".join([ShiftType.to_string(baseline.schedule[nurse_id][d]) 
                                 for d in range(10)])
        print(f"  Nurse {nurse_id}: {schedule_str}")
    
    print("\nNeighbor schedule (after single shift change):")
    for nurse_id in range(min(3, len(instance['nurses']))):
        schedule_str = " ".join([ShiftType.to_string(neighbor.schedule[nurse_id][d]) 
                                 for d in range(10)])
        print(f"  Nurse {nurse_id}: {schedule_str}")
    
    # Find what changed
    print("\nWhat changed:")
    for nurse_id in range(len(instance['nurses'])):
        for day in range(instance['period']):
            if baseline.schedule[nurse_id][day] != neighbor.schedule[nurse_id][day]:
                old_shift = ShiftType.to_string(baseline.schedule[nurse_id][day])
                new_shift = ShiftType.to_string(neighbor.schedule[nurse_id][day])
                print(f"  Nurse {nurse_id}, Day {day}: {old_shift} → {new_shift}")
    
    baseline_pen = evaluate_solution(baseline, instance)
    neighbor_pen = evaluate_solution(neighbor, instance)
    delta = neighbor_pen - baseline_pen
    
    print(f"\nPenalty change: {baseline_pen} → {neighbor_pen} (Δ = {delta:+d})")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("All operators have been tested.")
print("Operators with >90% success rate are working well.")
print("Operators with improving moves are suitable for Hill Climbing.")
print("="*80)