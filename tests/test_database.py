'''
Tests for the SQLite results database and the SQL queries.

The database is built fresh from results/raw into a temporary folder, so
these tests check the build pipeline itself, not a committed binary file.
The query results are cross-checked against the independent pandas
analysis in results/analysis/: two different pipelines must agree.
'''

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'experiments'))

import build_database  # noqa: E402


@pytest.fixture(scope='module')
def db(tmp_path_factory):
    path = tmp_path_factory.mktemp('db') / 'results.db'
    build_database.build(path)
    con = sqlite3.connect(path)
    yield con
    con.close()


def run_sql(con, filename):
    cur = con.execute((REPO_ROOT / 'sql' / filename).read_text())
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def read_csv(name):
    with open(REPO_ROOT / 'results' / 'analysis' / name) as f:
        return list(csv.DictReader(f))


# --- Data integrity --------------------------------------------------------

def test_all_runs_loaded(db):
    assert db.execute('SELECT COUNT(*) FROM runs').fetchone()[0] == 2800
    assert db.execute('SELECT COUNT(*) FROM instances').fetchone()[0] == 20


def test_instance_counts_per_scale(db):
    counts = dict(db.execute('SELECT scale, COUNT(*) FROM instances GROUP BY scale'))
    assert counts == {'sprint': 10, 'medium': 5, 'long': 5}


def test_every_configuration_has_ten_seeds(db):
    bad = db.execute('''
        SELECT instance_id, algorithm_id, lc, COUNT(*) AS n
        FROM runs GROUP BY instance_id, algorithm_id, lc
        HAVING n <> 10''').fetchall()
    assert bad == []


def test_hc_rows_have_no_lc_and_schc_rows_do(db):
    assert db.execute('''
        SELECT COUNT(*) FROM runs JOIN algorithms USING (algorithm_id)
        WHERE (name = 'HC') <> (lc IS NULL)''').fetchone()[0] == 0


def test_duplicate_run_is_rejected(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute('''
            INSERT INTO runs (instance_id, algorithm_id, lc, seed, baseline_penalty,
                              final_penalty, iterations, improving_moves, bound_updates,
                              elapsed_seconds)
            SELECT instance_id, algorithm_id, lc, seed, baseline_penalty, final_penalty,
                   iterations, improving_moves, bound_updates, elapsed_seconds
            FROM runs WHERE algorithm_id = 1 LIMIT 1''')
    db.rollback()


# --- Queries agree with the pandas analysis --------------------------------

def test_optimal_lc_query_matches_analysis(db):
    sql_rows = {(r['scale'], r['algorithm']): r for r in run_sql(db, '01_optimal_lc.sql')}
    expected = read_csv('optimal_lc_table.csv')
    assert len(sql_rows) == len(expected) == 9
    for e in expected:
        r = sql_rows[(e['scale'], e['variant'])]
        assert r['optimal_lc'] == int(e['optimal_lc'])
        assert r['mean_penalty'] == pytest.approx(float(e['mean']), abs=0.005)
        assert r['pct_reduction_vs_hc'] == pytest.approx(-float(e['vs_hc_pct']), abs=0.05)


def test_head_to_head_pairs_every_run(db):
    rows = run_sql(db, '02_head_to_head_vs_hc.sql')
    pairs = {r['scale']: r['paired_runs'] for r in rows}
    assert pairs == {'sprint': 100, 'medium': 50, 'long': 50}
    for r in rows:
        assert r['wins'] + r['ties'] + r['losses'] == r['paired_runs']


def test_head_to_head_mean_saving_matches_analysis(db):
    rows = {(r['scale'], r['algorithm']): r for r in run_sql(db, '02_head_to_head_vs_hc.sql')}
    for e in read_csv('optimal_lc_table.csv'):
        assert rows[(e['scale'], e['variant'])]['mean_penalty_saved'] == \
            pytest.approx(-float(e['vs_hc']), abs=0.005)


def test_cost_quality_query_matches_summary_table(db):
    rows = {(r['scale'], r['algorithm'], r['lc']): r
            for r in run_sql(db, '03_cost_quality_tradeoff.sql')}
    expected = [e for e in read_csv('summary_table.csv') if e['algorithm'] != 'HC']
    assert len(rows) == len(expected)
    for e in expected:
        r = rows[(e['scale'], e['algorithm'], int(e['lc']))]
        assert r['mean_penalty'] == pytest.approx(float(e['mean']), abs=0.005)
