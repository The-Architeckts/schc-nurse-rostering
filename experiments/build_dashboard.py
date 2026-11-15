'''
Build the Results Dashboard
===========================
Runs the SQL queries in sql/ against the results database and writes a
self-contained dashboard to docs/index.html (served by GitHub Pages).

The page has no external dependencies: the query results are embedded as
JSON and drawn as SVG by plain JavaScript. The output is deterministic, so
CI can check that the committed dashboard matches the data.

Usage (from the repository root):
    python experiments/build_database.py      # if the database is missing
    python experiments/build_dashboard.py [db_path] [output_html]

Standard library only.
'''

import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR   = REPO_ROOT / 'sql'
TEMPLATE  = Path(__file__).resolve().parent / 'dashboard_template.html'


def query(con, sql):
    cur  = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def collect(db_path):
    con = sqlite3.connect(db_path)
    data = {
        'optimal':     query(con, (SQL_DIR / '01_optimal_lc.sql').read_text()),
        'headToHead':  query(con, (SQL_DIR / '02_head_to_head_vs_hc.sql').read_text()),
        'costQuality': query(con, (SQL_DIR / '03_cost_quality_tradeoff.sql').read_text()),
        'hc': query(con, '''
            SELECT scale, ROUND(mean_penalty, 2) AS mean_penalty,
                   ROUND(mean_seconds, 1) AS mean_seconds
            FROM v_config_summary WHERE algorithm = 'HC' '''),
        'kpi': query(con, '''
            SELECT COUNT(*)                                   AS runs,
                   COUNT(DISTINCT instance_id)                AS instances,
                   ROUND(SUM(elapsed_seconds) / 3600.0, 0)    AS cpu_hours
            FROM runs''')[0],
    }
    con.close()
    return data


def build(db_path, out_path):
    data = collect(db_path)
    html = TEMPLATE.read_text().replace(
        '/*__DATA__*/null', json.dumps(data, sort_keys=True, separators=(',', ':')))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    return out_path


if __name__ == '__main__':
    db  = sys.argv[1] if len(sys.argv) > 1 else REPO_ROOT / 'results' / 'schc_results.db'
    out = sys.argv[2] if len(sys.argv) > 2 else REPO_ROOT / 'docs' / 'index.html'
    if not Path(db).exists():
        sys.exit(f'Database not found: {db}. Run experiments/build_database.py first.')
    print(f'Dashboard written to {build(db, out)}')
