'''
End-to-end checks that the committed outputs are reproducible from the
committed raw data. If someone edits the raw results, the analysis code
or the SQL without regenerating the outputs, these tests fail.
'''

import csv
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'experiments'))

ANALYSIS_FILES = ['summary_table.csv', 'optimal_lc_table.csv',
                  'wilcoxon_tests.csv', 'cross_scale_summary.csv']


@pytest.fixture(scope='module')
def regenerated_analysis(tmp_path_factory):
    out = tmp_path_factory.mktemp('analysis')
    subprocess.run([sys.executable, str(REPO_ROOT / 'experiments' / 'analyse_results.py'), str(out)],
                   check=True, capture_output=True)
    return out


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize('name', ANALYSIS_FILES)
def test_analysis_tables_are_reproducible(regenerated_analysis, name):
    committed   = rows(REPO_ROOT / 'results' / 'analysis' / name)
    regenerated = rows(regenerated_analysis / name)
    assert len(committed) == len(regenerated)
    for c, r in zip(committed, regenerated):
        assert c.keys() == r.keys()
        for key in c:
            try:
                assert float(c[key]) == pytest.approx(float(r[key]), rel=1e-9, nan_ok=True)
            except ValueError:
                assert c[key] == r[key]


def test_analysis_report_is_reproducible(regenerated_analysis):
    # Skip the header, which contains the generation timestamp.
    committed   = (REPO_ROOT / 'results' / 'analysis' / 'analysis_report.txt').read_text().splitlines()[5:]
    regenerated = (regenerated_analysis / 'analysis_report.txt').read_text().splitlines()[5:]
    assert committed == regenerated


def test_committed_dashboard_is_up_to_date(tmp_path):
    import build_database
    import build_dashboard
    db = tmp_path / 'results.db'
    build_database.build(db)
    html = build_dashboard.build(db, tmp_path / 'index.html').read_text()
    assert html == (REPO_ROOT / 'docs' / 'index.html').read_text(), \
        'docs/index.html is stale: run experiments/build_database.py then experiments/build_dashboard.py'
