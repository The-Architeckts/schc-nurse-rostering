'''
Statistical Analysis - SCHC on INRC-I
======================================
Loads the final Falcon results CSVs, computes descriptive statistics,
runs Wilcoxon signed-rank tests for pairwise comparisons, and
produces the tables reported in the dissertation.

This is the script that was run on the Falcon HPC cluster in May 2026
to produce results/analysis/. The only changes since are the input
and output paths, which now point at this repository's layout.

Run from the repository root:
    python experiments/analyse_results.py [output_dir]

    output_dir defaults to results/analysis

Output:
    summary_table.csv        - mean/std per algorithm/scale/Lc
    optimal_lc_table.csv     - optimal Lc per variant per scale
    wilcoxon_tests.csv       - pairwise statistical tests
    cross_scale_summary.csv  - variant comparison at optimal Lc
    analysis_report.txt      - full human-readable report

Requires pandas, numpy and scipy.
'''

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR   = REPO_ROOT / 'results' / 'raw'

# ---------------------------------------------------------------------------
# VALID OUTPUT DIRECTORIES
# ---------------------------------------------------------------------------
# Each entry is one Slurm array task. The original Falcon directory names
# (which carried a start timestamp) are given in the comments. For long04
# and long05, earlier runs produced by pre-fix code were discarded and only
# the most recent runs are used.

VALID_DIRS = [
    # Sprint (job 285350)
    'sprint_01',   # sprint_01_20260424_191432
    'sprint_02',   # sprint_02_20260424_191432
    'sprint_03',   # sprint_03_20260424_191432
    'sprint_04',   # sprint_04_20260424_191432
    'sprint_05',   # sprint_05_20260424_211940
    'sprint_06',   # sprint_06_20260424_211940
    'sprint_07',   # sprint_07_20260424_212040
    'sprint_08',   # sprint_08_20260424_212540
    'sprint_09',   # sprint_09_20260424_231847
    'sprint_10',   # sprint_10_20260424_232347
    # Medium (job 291104)
    'medium_01',   # medium_01_20260426_192108
    'medium_02',   # medium_02_20260426_192108
    'medium_03',   # medium_03_20260426_192108
    'medium_04',   # medium_04_20260426_192108
    'medium_05',   # medium_05_20260427_153600
    # Long (job 291105)
    'long_01',     # long_01_20260427_170212
    'long_02',     # long_02_20260427_170212
    'long_03',     # long_03_20260427_170212
    'long_04',     # long_04_20260428_130348
    'long_05',     # long_05_20260429_201543
]

OUTPUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / 'results' / 'analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Empirically determined optimal Lc per variant per scale
# (lowest mean penalty in the Lc sweep, see summary_table.csv)
OPTIMAL_LC = {
    ('all',   'sprint'): 1500,
    ('acp',   'sprint'): 1500,
    ('imp',   'sprint'): 25,
    ('all',   'medium'): 2500,
    ('acp',   'medium'): 2500,
    ('imp',   'medium'): 15,
    ('all',   'long'):   2500,
    ('acp',   'long'):   2500,
    ('imp',   'long'):   15,
}

# ---------------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------------

print("Loading data...")
dfs = []
for d in VALID_DIRS:
    csv_path = RAW_DIR / d / 'results.csv'
    if not csv_path.exists():
        print(f"  WARNING: {csv_path} not found, skipping")
        continue
    df = pd.read_csv(csv_path)
    # Infer scale from directory name
    scale = d.split('_')[0]
    df['scale'] = scale
    dfs.append(df)

data = pd.concat(dfs, ignore_index=True)

# Normalise algorithm column
data['algorithm'] = data['algorithm'].str.strip()
data['lc'] = pd.to_numeric(data['lc'], errors='coerce')

print(f"  Loaded {len(data):,} rows from {len(dfs)} files")
print(f"  Scales: {sorted(data['scale'].unique())}")
print(f"  Algorithms: {sorted(data['algorithm'].unique())}")
print()


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def wilcoxon_test(a, b, alternative='two-sided'):
    '''
    Wilcoxon signed-rank test. Returns statistic, p-value, and effect size r.
    Falls back to NaN if insufficient data.

    Samples are paired by position: within a scale, rows are ordered by
    instance and then by run (random seed), so a[i] and b[i] share the
    same instance and seed.
    '''
    try:
        if len(a) < 10 or len(b) < 10:
            return np.nan, np.nan, np.nan
        stat, p = stats.wilcoxon(a, b, alternative=alternative)
        # Effect size r = Z / sqrt(N), with Z recovered from the p-value
        z = stats.norm.ppf(p / 2) if p > 0 else 0
        r = abs(z) / np.sqrt(len(a))
        return stat, p, r
    except Exception:
        return np.nan, np.nan, np.nan


def get_finals(data, scale, algorithm, lc=None):
    '''Extract final_penalty values for a given config.'''
    mask = (data['scale'] == scale) & (data['algorithm'] == algorithm)
    if lc is not None:
        mask &= (data['lc'] == lc)
    return data[mask]['final_penalty'].values


def interpret_p(p):
    if np.isnan(p):
        return 'N/A'
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    else:
        return 'n.s.'


# ---------------------------------------------------------------------------
# 1. DESCRIPTIVE STATISTICS - ALL CONFIGURATIONS
# ---------------------------------------------------------------------------

print("Computing descriptive statistics...")

summary_rows = []
for scale in ['sprint', 'medium', 'long']:
    scale_data = data[data['scale'] == scale]

    # HC
    hc_data = scale_data[scale_data['algorithm'] == 'HC']['final_penalty']
    summary_rows.append({
        'scale': scale, 'algorithm': 'HC', 'lc': 'N/A',
        'n': len(hc_data),
        'mean': hc_data.mean(), 'std': hc_data.std(),
        'min': hc_data.min(), 'max': hc_data.max(),
        'median': hc_data.median()
    })

    # SCHC variants
    for variant in ['all', 'acp', 'imp']:
        algo = f'SCHC-{variant}'
        variant_data = scale_data[scale_data['algorithm'] == algo]
        for lc in sorted(variant_data['lc'].dropna().unique()):
            lc_data = variant_data[variant_data['lc'] == lc]['final_penalty']
            summary_rows.append({
                'scale': scale, 'algorithm': algo, 'lc': int(lc),
                'n': len(lc_data),
                'mean': lc_data.mean(), 'std': lc_data.std(),
                'min': lc_data.min(), 'max': lc_data.max(),
                'median': lc_data.median()
            })

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(OUTPUT_DIR / 'summary_table.csv', index=False)
print(f"  Saved summary_table.csv ({len(summary_df)} rows)")


# ---------------------------------------------------------------------------
# 2. OPTIMAL LC TABLE
# ---------------------------------------------------------------------------

print("Computing optimal Lc table...")

opt_rows = []
for scale in ['sprint', 'medium', 'long']:
    scale_data = data[data['scale'] == scale]
    hc_mean = scale_data[scale_data['algorithm'] == 'HC']['final_penalty'].mean()

    for variant in ['all', 'acp', 'imp']:
        algo    = f'SCHC-{variant}'
        opt_lc  = OPTIMAL_LC[(variant, scale)]
        opt_data = scale_data[
            (scale_data['algorithm'] == algo) &
            (scale_data['lc'] == opt_lc)
        ]['final_penalty']

        if len(opt_data) == 0:
            continue

        opt_rows.append({
            'scale':      scale,
            'variant':    algo,
            'optimal_lc': opt_lc,
            'mean':       opt_data.mean(),
            'std':        opt_data.std(),
            'min':        opt_data.min(),
            'max':        opt_data.max(),
            'hc_mean':    hc_mean,
            'vs_hc':      opt_data.mean() - hc_mean,
            'vs_hc_pct':  (opt_data.mean() - hc_mean) / hc_mean * 100,
        })

opt_df = pd.DataFrame(opt_rows)
opt_df.to_csv(OUTPUT_DIR / 'optimal_lc_table.csv', index=False)
print(f"  Saved optimal_lc_table.csv")


# ---------------------------------------------------------------------------
# 3. WILCOXON SIGNED-RANK TESTS
# ---------------------------------------------------------------------------

print("Running Wilcoxon signed-rank tests...")

wilcoxon_rows = []
comparisons = [
    ('SCHC-all', 'HC'),
    ('SCHC-acp', 'HC'),
    ('SCHC-imp', 'HC'),
    ('SCHC-acp', 'SCHC-all'),
    ('SCHC-imp', 'SCHC-all'),
    ('SCHC-imp', 'SCHC-acp'),
]

for scale in ['sprint', 'medium', 'long']:
    for algo_a, algo_b in comparisons:
        # Get optimal Lc for each
        lc_a = None
        lc_b = None

        if algo_a.startswith('SCHC-'):
            v = algo_a.replace('SCHC-', '')
            lc_a = OPTIMAL_LC.get((v, scale))
        if algo_b.startswith('SCHC-'):
            v = algo_b.replace('SCHC-', '')
            lc_b = OPTIMAL_LC.get((v, scale))

        vals_a = get_finals(data, scale, algo_a, lc_a)
        vals_b = get_finals(data, scale, algo_b, lc_b)

        # Match lengths by taking min
        n = min(len(vals_a), len(vals_b))
        if n < 5:
            continue

        vals_a = vals_a[:n]
        vals_b = vals_b[:n]

        stat, p, r = wilcoxon_test(vals_a, vals_b)

        wilcoxon_rows.append({
            'scale':     scale,
            'algo_a':    algo_a,
            'lc_a':      lc_a if lc_a else 'N/A',
            'algo_b':    algo_b,
            'lc_b':      lc_b if lc_b else 'N/A',
            'mean_a':    vals_a.mean(),
            'mean_b':    vals_b.mean(),
            'mean_diff': vals_a.mean() - vals_b.mean(),
            'statistic': stat,
            'p_value':   p,
            'effect_r':  r,
            'sig':       interpret_p(p),
            'n':         n,
        })

wilcoxon_df = pd.DataFrame(wilcoxon_rows)
wilcoxon_df.to_csv(OUTPUT_DIR / 'wilcoxon_tests.csv', index=False)
print(f"  Saved wilcoxon_tests.csv ({len(wilcoxon_df)} tests)")


# ---------------------------------------------------------------------------
# 4. CROSS-SCALE SUMMARY
# ---------------------------------------------------------------------------

print("Computing cross-scale summary...")

cross_rows = []
for scale in ['sprint', 'medium', 'long']:
    scale_data = data[data['scale'] == scale]
    hc_mean    = scale_data[scale_data['algorithm'] == 'HC']['final_penalty'].mean()
    hc_std     = scale_data[scale_data['algorithm'] == 'HC']['final_penalty'].std()

    cross_rows.append({
        'scale': scale, 'algorithm': 'HC', 'optimal_lc': 'N/A',
        'mean': round(hc_mean, 2), 'std': round(hc_std, 2),
        'vs_hc': 0.0, 'sig': 'baseline'
    })

    for variant in ['all', 'acp', 'imp']:
        algo   = f'SCHC-{variant}'
        opt_lc = OPTIMAL_LC[(variant, scale)]
        vals   = get_finals(data, scale, algo, opt_lc)
        hc_v   = get_finals(data, scale, 'HC')
        n      = min(len(vals), len(hc_v))
        _, p, _ = wilcoxon_test(vals[:n], hc_v[:n])

        cross_rows.append({
            'scale':      scale,
            'algorithm':  algo,
            'optimal_lc': opt_lc,
            'mean':       round(vals.mean(), 2),
            'std':        round(vals.std(), 2),
            'vs_hc':      round(vals.mean() - hc_mean, 2),
            'sig':        interpret_p(p),
        })

cross_df = pd.DataFrame(cross_rows)
cross_df.to_csv(OUTPUT_DIR / 'cross_scale_summary.csv', index=False)
print(f"  Saved cross_scale_summary.csv")


# ---------------------------------------------------------------------------
# 5. HUMAN-READABLE REPORT
# ---------------------------------------------------------------------------

print("Writing analysis report...")

report_lines = []
report_lines.append("=" * 80)
report_lines.append("STATISTICAL ANALYSIS REPORT")
report_lines.append("SCHC Applied to INRC-I Nurse Rostering Problem")
report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append("=" * 80)

for scale in ['sprint', 'medium', 'long']:
    scale_data = data[data['scale'] == scale]
    hc_mean    = scale_data[scale_data['algorithm'] == 'HC']['final_penalty'].mean()
    hc_std     = scale_data[scale_data['algorithm'] == 'HC']['final_penalty'].std()
    n_inst     = scale_data['instance'].nunique()

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append(f"{scale.upper()} INSTANCES  (n={n_inst} instances x 10 runs)")
    report_lines.append("=" * 80)
    report_lines.append(f"HC baseline:  mean={hc_mean:.2f}  std={hc_std:.2f}")
    report_lines.append("")

    report_lines.append(f"{'Algorithm':<14} {'Opt Lc':>8} {'Mean':>8} "
                        f"{'Std':>7} {'Best':>7} {'Worst':>7} "
                        f"{'vs HC':>8} {'p-value':>10} {'sig':>5}")
    report_lines.append("-" * 80)

    for variant in ['all', 'acp', 'imp']:
        algo   = f'SCHC-{variant}'
        opt_lc = OPTIMAL_LC[(variant, scale)]
        vals   = get_finals(data, scale, algo, opt_lc)
        hc_v   = get_finals(data, scale, 'HC')
        n      = min(len(vals), len(hc_v))
        _, p, r = wilcoxon_test(vals[:n], hc_v[:n])

        report_lines.append(
            f"{algo:<14} {opt_lc:>8} {vals.mean():>8.2f} "
            f"{vals.std():>7.2f} {vals.min():>7.0f} {vals.max():>7.0f} "
            f"{vals.mean()-hc_mean:>+8.2f} "
            f"{p:>10.4f} {interpret_p(p):>5}"
        )

    report_lines.append("")
    report_lines.append("Pairwise comparisons (Wilcoxon signed-rank, at optimal Lc):")
    report_lines.append(f"  {'Comparison':<25} {'Mean diff':>10} {'p-value':>10} "
                        f"{'Effect r':>10} {'sig':>5}")
    report_lines.append("  " + "-" * 60)

    pairs = [('SCHC-acp', 'SCHC-all'),
             ('SCHC-imp', 'SCHC-all'),
             ('SCHC-imp', 'SCHC-acp')]

    for algo_a, algo_b in pairs:
        v_a    = algo_a.replace('SCHC-', '')
        v_b    = algo_b.replace('SCHC-', '')
        lc_a   = OPTIMAL_LC[(v_a, scale)]
        lc_b   = OPTIMAL_LC[(v_b, scale)]
        vals_a = get_finals(data, scale, algo_a, lc_a)
        vals_b = get_finals(data, scale, algo_b, lc_b)
        n      = min(len(vals_a), len(vals_b))
        _, p, r = wilcoxon_test(vals_a[:n], vals_b[:n])
        diff   = vals_a.mean() - vals_b.mean()
        label  = f"{algo_a} vs {algo_b}"
        report_lines.append(
            f"  {label:<25} {diff:>+10.2f} {p:>10.4f} "
            f"{r:>10.4f} {interpret_p(p):>5}"
        )

# Lc sensitivity section
report_lines.append("")
report_lines.append("=" * 80)
report_lines.append("Lc SENSITIVITY ANALYSIS")
report_lines.append("=" * 80)
report_lines.append("")
report_lines.append("Optimal Lc per variant per scale:")
report_lines.append(f"  {'Scale':<10} {'SCHC-all':>10} {'SCHC-acp':>10} {'SCHC-imp':>10}")
report_lines.append("  " + "-" * 44)
for scale in ['sprint', 'medium', 'long']:
    report_lines.append(
        f"  {scale:<10} "
        f"{OPTIMAL_LC[('all', scale)]:>10} "
        f"{OPTIMAL_LC[('acp', scale)]:>10} "
        f"{OPTIMAL_LC[('imp', scale)]:>10}"
    )

report_lines.append("")
report_lines.append("Key finding: SCHC-imp optimal Lc is scale-invariant (~15-25),")
report_lines.append("while SCHC-all and SCHC-acp optimal Lc is consistently 1500-2500.")
report_lines.append("This reflects SCHC-imp's low improving move rate on the NRP (~1-10%),")
report_lines.append("requiring a smaller Lc to achieve equivalent bound update frequency.")

report_text = "\n".join(report_lines)
print(report_text)

report_path = OUTPUT_DIR / 'analysis_report.txt'
with open(report_path, 'w') as f:
    f.write(report_text)

print()
print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print(f"Output directory: {OUTPUT_DIR}/")
