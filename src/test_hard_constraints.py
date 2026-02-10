"""
Test hard constraint checking with valid and invalid solutions.
"""

from data_loader import load_instance
from solution import Solution
from models import ShiftType
from constraints import evaluate_solution, check_coverage_violations, check_single_assignment_violations
from constructors import greedy_constructor

# Load instance
instance = load_instance('data/inrc1/INRC1_sprint01.json')

print("="*80)
print("TEST 1: BASELINE SOLUTION (SHOULD BE FEASIBLE)")
print("="*80)

baseline = greedy_constructor(instance)

coverage_viol = check_coverage_violations(baseline, instance)
single_viol = check_single_assignment_violations(baseline)
total_penalty = evaluate_solution(baseline, instance)

print(f"Coverage violations: {coverage_viol}")
print(f"Single assignment violations: {single_viol}")
print(f"Total penalty: {total_penalty}")
print(f"Expected: 0 hard violations, penalty = 153 (soft only)")

if coverage_viol == 0 and single_viol == 0:
    print("✅ PASSED: Baseline solution is feasible")
else:
    print("❌ FAILED: Baseline should have no hard violations!")

print("\n" + "="*80)
print("TEST 2: EMPTY SOLUTION (SHOULD HAVE MASSIVE VIOLATIONS)")
print("="*80)

# Create empty solution (all nurses OFF)
empty_solution = Solution(len(instance['nurses']), instance['period'])

coverage_viol = check_coverage_violations(empty_solution, instance)
single_viol = check_single_assignment_violations(empty_solution)
total_penalty = evaluate_solution(empty_solution, instance)

print(f"Coverage violations: {coverage_viol}")
print(f"Single assignment violations: {single_viol}")
print(f"Total penalty: {total_penalty}")
print(f"Expected: {len(instance['coverage'])} coverage violations")

if coverage_viol == len(instance['coverage']):
    print("✅ PASSED: Empty solution correctly detected all coverage violations")
else:
    print(f"❌ FAILED: Expected {len(instance['coverage'])} coverage violations, got {coverage_viol}")

if total_penalty >= 10**6:
    print("✅ PASSED: Hard violations result in penalty ≥ 10^6")
else:
    print("❌ FAILED: Hard violations should result in penalty ≥ 10^6")

print("\n" + "="*80)
print("TEST 3: PARTIAL SOLUTION (SOME COVERAGE MISSING)")
print("="*80)

# Create solution where only first 5 nurses work
partial_solution = Solution(len(instance['nurses']), instance['period'])

# Copy first 5 nurses from baseline
for nurse_id in range(5):
    partial_solution.schedule[nurse_id] = baseline.schedule[nurse_id].copy()

coverage_viol = check_coverage_violations(partial_solution, instance)
single_viol = check_single_assignment_violations(partial_solution)
total_penalty = evaluate_solution(partial_solution, instance)

print(f"Coverage violations: {coverage_viol}")
print(f"Single assignment violations: {single_viol}")
print(f"Total penalty: {total_penalty}")

if coverage_viol > 0:
    print("✅ PASSED: Partial solution correctly detected coverage violations")
else:
    print("❌ FAILED: Partial solution should have coverage violations")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("If all tests passed, hard constraint checking is working correctly!")
print("Penalty formula: (hard_violations × 10^6) + soft_violations")
print("="*80)