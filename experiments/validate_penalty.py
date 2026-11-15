'''
Penalty Function Validation
============================
Evaluates the best-known solutions (BKS) published by Toffolo et al. for
the INRC-I benchmark with this project's penalty function, and compares
the result against the published penalty.

This check was carried out before the final experiments. Discrepancies
are small (0 to 7 points) and always in the direction of
under-penalisation, so absolute penalties reported in this project are
marginally optimistic, while comparisons between algorithms, which all
use the same evaluator, are unaffected.

Solution files: data/toffolo_bks/*.xml
Source: https://benchmark.gent.cs.kuleuven.be/nrp

Usage (from the repository root):
    python experiments/validate_penalty.py
'''

import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

from data_loader import load_instance
from constraints import evaluate_solution
from solution import Solution
from models import ShiftType

# Published best-known penalties (Toffolo et al.)
BKS = {
    'sprint01': 56, 'sprint02': 58, 'sprint03': 51,
    'sprint04': 59, 'sprint05': 58,
    'medium01': 240,
    'long05':   284,
}

START_DATE = date(2010, 1, 1)   # all INRC-I instances start on 1 Jan 2010


def load_bks_solution(xml_path, instance):
    sol = Solution(len(instance['nurses']), instance['period'])
    for a in ET.parse(xml_path).getroot().findall('Assignment'):
        d     = datetime.strptime(a.find('Date').text, '%Y-%m-%d').date()
        nurse = int(a.find('Employee').text)
        shift = getattr(ShiftType, a.find('ShiftType').text)
        sol.assign_shift(nurse, (d - START_DATE).days, shift)
    return sol


def main():
    print(f"{'Instance':<10} {'Published':>10} {'Ours':>6} {'Diff':>6}")
    print("-" * 36)
    for name, published in BKS.items():
        instance = load_instance(str(REPO_ROOT / 'data' / 'inrc1' / f'INRC1_{name}.json'))
        sol      = load_bks_solution(REPO_ROOT / 'data' / 'toffolo_bks' / f'{name}.xml', instance)
        ours     = evaluate_solution(sol, instance)
        print(f"{name:<10} {published:>10} {ours:>6} {ours - published:>+6}")


if __name__ == '__main__':
    main()
