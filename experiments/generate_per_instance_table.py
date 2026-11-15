"""
Prints the per-instance results table (mean final penalty at optimal Lc)
used in the dissertation, reading the final results in results/raw/.

Usage:
    python generate_per_instance_table.py

It will print a LaTeX table ready to paste into the dissertation.
"""
import csv
import os
import glob
from collections import defaultdict

RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'raw')

OPTIMAL = {
    'sprint': {'HC': None, 'SCHC-all': '1500', 'SCHC-acp': '1500', 'SCHC-imp': '25'},
    'medium': {'HC': None, 'SCHC-all': '2500', 'SCHC-acp': '2500', 'SCHC-imp': '15'},
    'long':   {'HC': None, 'SCHC-all': '2500', 'SCHC-acp': '2500', 'SCHC-imp': '15'},
}

BASE_DIRS = {
    'sprint': sorted(glob.glob(os.path.join(RAW_DIR, 'sprint_*/results.csv'))),
    'medium': sorted(glob.glob(os.path.join(RAW_DIR, 'medium_*/results.csv'))),
    'long':   sorted(glob.glob(os.path.join(RAW_DIR, 'long_*/results.csv'))),
}

# ── Debug: show what was found ────────────────────────────────────────
print(f"Looking in: {os.path.abspath(RAW_DIR)}\n")
for scale, paths in BASE_DIRS.items():
    print(f"  {scale}: found {len(paths)} result file(s)")
print()

def extract_instance_number(path):
    dirname = os.path.basename(os.path.dirname(path))
    parts = dirname.split('_')
    return parts[1] if len(parts) > 1 else '??'

def load_results(paths, scale):
    instance_data = {}
    for path in paths:
        num = extract_instance_number(path)
        rows = defaultdict(list)
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    algo = row.get('algorithm', '').strip()
                    lc   = row.get('lc', '').strip()
                    fp   = row.get('final_penalty', '')
                    if not fp:
                        continue
                    opt = OPTIMAL[scale].get(algo)
                    if algo == 'HC':
                        rows['HC'].append(float(fp))
                    elif opt and lc == opt:
                        rows[algo].append(float(fp))
        except Exception as e:
            print(f"  WARNING: could not read {path}: {e}")
            continue
        instance_data[num] = {
            algo: (sum(v) / len(v) if v else None)
            for algo, v in rows.items()
        }
    return instance_data

def fmt(v):
    return f"{v:.1f}" if v is not None else '--'

def print_latex_table(scale, data):
    if not data:
        print(f"% No data for {scale} scale\n")
        return
    opt_all = OPTIMAL[scale]['SCHC-all']
    opt_acp = OPTIMAL[scale]['SCHC-acp']
    opt_imp = OPTIMAL[scale]['SCHC-imp']
    cap = scale.capitalize()
    print(r"\begin{table}[H]")
    print(r"\centering")
    print(
        f"\\caption{{Mean final penalty (10 runs) at optimal $L_c$ per instance "
        f"--- {cap} scale. Optimal $L_c$: SCHC-all $= {opt_all}$, "
        f"SCHC-acp $= {opt_acp}$, SCHC-imp $= {opt_imp}$.}}"
    )
    print(f"\\label{{tab:per_instance_{scale}}}")
    print(r"\small")
    print(r"\begin{tabular}{lrrrr}")
    print(r"\toprule")
    print(r"Instance & HC & SCHC-all & SCHC-acp & SCHC-imp \\")
    print(r"\midrule")
    for num in sorted(data.keys()):
        d  = data[num]
        n  = int(num)
        label = f"{scale}\\_{n:02d}"
        hc = fmt(d.get('HC'))
        sa = fmt(d.get('SCHC-all'))
        sc = fmt(d.get('SCHC-acp'))
        si = fmt(d.get('SCHC-imp'))
        print(f"  {label} & {hc} & {sa} & {sc} & {si} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")
    print()

for scale in ['sprint', 'medium', 'long']:
    paths = BASE_DIRS[scale]
    if not paths:
        print(f"% WARNING: No {scale} results found in {os.path.abspath(RAW_DIR)}\n")
        continue
    data = load_results(paths, scale)
    print_latex_table(scale, data)