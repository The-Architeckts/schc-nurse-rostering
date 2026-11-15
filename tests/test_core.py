'''
Regression tests for the final implementation.

These pin the behaviour of the code that produced results/raw/:
the greedy baseline, hard constraint handling, agreement with
published best-known solutions, and exact reproduction of individual
Falcon runs from their random seeds.

Run from the repository root:
    python -m pytest tests/
'''

import csv
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
sys.path.insert(0, str(REPO_ROOT / 'experiments'))

from data_loader import load_instance
from constructors import greedy_constructor
from constraints import (evaluate_solution, check_coverage_violations,
                         check_single_assignment_violations)
from solution import Solution
from algorithms.hill_climbing import HillClimbing
from algorithms.schc import SCHC


def instance(name):
    return load_instance(str(REPO_ROOT / 'data' / 'inrc1' / f'INRC1_{name}.json'))


def falcon_row(scale_dir, algorithm, lc, run):
    path = REPO_ROOT / 'results' / 'raw' / scale_dir / 'results.csv'
    with open(path) as f:
        for row in csv.DictReader(f):
            if (row['algorithm'] == algorithm and row['lc'] == str(lc)
                    and row['run'] == str(run)):
                return row
    raise LookupError((scale_dir, algorithm, lc, run))


@pytest.fixture(scope='module')
def sprint01():
    inst = instance('sprint01')
    return inst, greedy_constructor(inst)


def test_greedy_baseline_is_feasible(sprint01):
    inst, baseline = sprint01
    assert check_coverage_violations(baseline, inst) == 0
    assert check_single_assignment_violations(baseline) == 0
    assert evaluate_solution(baseline, inst) == 254


def test_empty_solution_is_heavily_penalised(sprint01):
    inst, _ = sprint01
    empty = Solution(len(inst['nurses']), inst['period'])
    assert evaluate_solution(empty, inst) >= 10**6


@pytest.mark.parametrize('name, expected', [
    ('sprint01', 56), ('sprint03', 51), ('medium01', 240),
])
def test_matches_published_best_known_solutions(name, expected):
    from validate_penalty import load_bks_solution
    inst = instance(name)
    sol  = load_bks_solution(REPO_ROOT / 'data' / 'toffolo_bks' / f'{name}.xml', inst)
    assert evaluate_solution(sol, inst) == expected


def test_hc_reproduces_falcon_run(sprint01):
    inst, baseline = sprint01
    expected = falcon_row('sprint_01', 'HC', 'N/A', 1)
    _, stats = HillClimbing(instance_data=inst, max_idle_iterations=2000,
                            random_seed=1).optimize(baseline, verbose=False)
    assert stats['final_penalty'] == int(expected['final_penalty'])
    assert stats['iterations'] == int(expected['iterations'])


def test_schc_all_reproduces_falcon_run(sprint01):
    inst, baseline = sprint01
    expected = falcon_row('sprint_01', 'SCHC-all', 100, 1)
    _, stats = SCHC(instance_data=inst, Lc=100, variant='all', random_seed=1,
                    print_interval=999999999).optimize(baseline, verbose=False)
    assert stats['final_penalty'] == int(expected['final_penalty'])
    assert stats['iterations'] == int(expected['iterations'])
    assert stats['bound_updates'] == int(expected['bound_updates'])
