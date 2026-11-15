import sys
sys.path.insert(0, 'src')
from data_loader import load_instance
from constraints import evaluate_solution
from solution import Solution
from models import ShiftType
import xml.etree.ElementTree as ET
from datetime import date, datetime

instance = load_instance('data/inrc1/INRC1_sprint05.json')
n_nurses = len(instance['nurses'])
n_days   = instance['period']

tree = ET.parse('sprint05.xml')
root = tree.getroot()

sol = Solution(n_nurses, n_days)

shift_map = {
    'E':  ShiftType.E,
    'L':  ShiftType.L,
    'D':  ShiftType.D,
    'N':  ShiftType.N,
    'DH': ShiftType.DH,
}

start_date = date(2010, 1, 1)

for assignment in root.findall('Assignment'):
    date_str  = assignment.find('Date').text
    emp_id    = int(assignment.find('Employee').text)
    shift_str = assignment.find('ShiftType').text

    d         = datetime.strptime(date_str, '%Y-%m-%d').date()
    day_index = (d - start_date).days

    if shift_str in shift_map:
        sol.assign_shift(emp_id, day_index, shift_map[shift_str])
    else:
        print(f"WARNING: unknown shift type '{shift_str}'")

penalty = evaluate_solution(sol, instance)
print(f"Our penalty function gives: {penalty}")
print(f"Official Toffolo score:     58")
print(f"Difference:                 {penalty - 58}")