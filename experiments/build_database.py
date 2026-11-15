'''
Build the SQLite Results Database
==================================
Loads every run in results/raw/*/results.csv into a normalised SQLite
database (schema in sql/schema.sql), then runs the three queries in sql/
as a check and prints their results.

Usage (from the repository root):
    python experiments/build_database.py [db_path]

    db_path defaults to results/schc_results.db

Query the database directly with, for example:
    sqlite3 results/schc_results.db < sql/01_optimal_lc.sql

Standard library only.
'''

import csv
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR   = REPO_ROOT / 'results' / 'raw'
SQL_DIR   = REPO_ROOT / 'sql'
DATA_DIR  = REPO_ROOT / 'data' / 'inrc1'

sys.path.insert(0, str(REPO_ROOT / 'src'))
from data_loader import load_instance  # noqa: E402

QUERIES = ['01_optimal_lc.sql', '02_head_to_head_vs_hc.sql', '03_cost_quality_tradeoff.sql']

ALGORITHMS = [
    ('HC',       None),
    ('SCHC-all', 'every iteration'),
    ('SCHC-acp', 'every accepted move'),
    ('SCHC-imp', 'every improving move'),
]

# Published best-known penalties (Toffolo et al.) for the instances used in
# the dissertation's validation and benchmark comparison.
BKS = {
    'sprint01': 56, 'sprint02': 58, 'sprint03': 51, 'sprint04': 59, 'sprint05': 58,
    'medium01': 240,
    'long01': 197, 'long02': 226, 'long03': 240, 'long04': 303, 'long05': 284,
}


def build(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    con.executescript((SQL_DIR / 'schema.sql').read_text())

    con.executemany('INSERT INTO algorithms (name, counter_rule) VALUES (?, ?)', ALGORITHMS)
    algo_ids = dict(con.execute('SELECT name, algorithm_id FROM algorithms'))

    instance_ids = {}
    run_rows = []
    for csv_path in sorted(RAW_DIR.glob('*/results.csv')):
        with open(csv_path, newline='') as f:
            rows = list(csv.DictReader(f))
        name  = rows[0]['instance'].replace('INRC1_', '')        # e.g. 'sprint01'
        scale = rows[0]['scale']
        inst  = load_instance(str(DATA_DIR / f'INRC1_{name}.json'))
        cur   = con.execute(
            'INSERT INTO instances (name, scale, nurses, days, bks_penalty) VALUES (?, ?, ?, ?, ?)',
            (name, scale, len(inst['nurses']), inst['period'], BKS.get(name)))
        instance_ids[name] = cur.lastrowid

        for r in rows:
            run_rows.append((
                instance_ids[name],
                algo_ids[r['algorithm']],
                None if r['lc'] == 'N/A' else int(r['lc']),
                int(r['run']),
                int(r['baseline_penalty']),
                int(r['final_penalty']),
                int(r['iterations']),
                int(r['improving_moves']),
                int(r['bound_updates']),
                float(r['elapsed_time']),
            ))

    con.executemany('''
        INSERT INTO runs (instance_id, algorithm_id, lc, seed, baseline_penalty,
                          final_penalty, iterations, improving_moves, bound_updates,
                          elapsed_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', run_rows)
    con.commit()
    con.execute('VACUUM')
    con.close()
    return len(instance_ids), len(run_rows)


def run_query(con, filename):
    cur  = con.execute((SQL_DIR / filename).read_text())
    cols = [d[0] for d in cur.description]
    return cols, cur.fetchall()


def print_table(cols, rows):
    widths = [max(len(str(c)), *(len(str(r[i])) for r in rows)) for i, c in enumerate(cols)]
    print('  '.join(str(c).ljust(w) for c, w in zip(cols, widths)))
    print('  '.join('-' * w for w in widths))
    for r in rows:
        print('  '.join(str(v).ljust(w) for v, w in zip(r, widths)))


if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else REPO_ROOT / 'results' / 'schc_results.db'
    n_inst, n_runs = build(db_path)
    print(f'Built {db_path}: {n_inst} instances, {n_runs} runs\n')

    con = sqlite3.connect(db_path)
    for q in QUERIES:
        print(f'== {q}')
        print_table(*run_query(con, q))
        print()
    con.close()
