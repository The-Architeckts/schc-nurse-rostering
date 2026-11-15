'''
Results Figures
===============
Draws the two summary figures shown in the README from the final
analysis tables in results/analysis/.

    results/figures/improvement_over_hc.png
        Mean penalty reduction relative to Hill Climbing, per variant and
        scale, at each variant's optimal Lc.

    results/figures/lc_sensitivity.png
        Mean final penalty against Lc (log scale) for each variant, one
        panel per problem scale, with the HC mean as a reference line.

Usage (from the repository root):
    python experiments/plot_results.py

Requires pandas and matplotlib.
'''

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd

REPO_ROOT    = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = REPO_ROOT / 'results' / 'analysis'
FIG_DIR      = REPO_ROOT / 'results' / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

SCALES   = ['sprint', 'medium', 'long']
VARIANTS = ['SCHC-all', 'SCHC-acp', 'SCHC-imp']
COLOURS  = {'SCHC-all': '#2a78d6', 'SCHC-acp': '#eb6834', 'SCHC-imp': '#1baf7a'}
MARKERS  = {'SCHC-all': 'o', 'SCHC-acp': 's', 'SCHC-imp': '^'}
SURFACE  = '#fcfcfb'
INK      = '#0b0b0b'
INK_2    = '#52514e'
GRID     = '#e4e3df'

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.edgecolor': GRID, 'axes.labelcolor': INK_2,
    'xtick.color': INK_2, 'ytick.color': INK_2,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE,
})


def improvement_figure():
    opt = pd.read_csv(ANALYSIS_DIR / 'optimal_lc_table.csv')
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    width = 0.26
    for i, variant in enumerate(VARIANTS):
        rows = opt[opt['variant'] == variant].set_index('scale').loc[SCALES]
        xs   = [s + (i - 1) * (width + 0.02) for s in range(len(SCALES))]
        vals = -rows['vs_hc_pct'].values
        ax.bar(xs, vals, width, color=COLOURS[variant], label=variant,
               edgecolor=SURFACE, linewidth=2)
        for x, v, lc in zip(xs, vals, rows['optimal_lc'].values):
            ax.text(x, v + 0.3, f'{v:.1f}%', ha='center', va='bottom',
                    fontsize=8.5, color=INK)
            ax.text(x, 0.4, f'Lc\n{lc}', ha='center', va='bottom',
                    fontsize=7, color=SURFACE)
    ax.set_xticks(range(len(SCALES)))
    ax.set_xticklabels([s.capitalize() for s in SCALES], color=INK)
    ax.set_ylabel('Mean penalty reduction vs HC (%)')
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 24)
    ax.legend(frameon=False, ncol=3, loc='upper left')
    ax.set_title('All three SCHC variants beat Hill Climbing at every scale '
                 '(Wilcoxon p < 0.001)', loc='left', color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'improvement_over_hc.png', facecolor=SURFACE)
    plt.close(fig)


def lc_sensitivity_figure():
    summ = pd.read_csv(ANALYSIS_DIR / 'summary_table.csv')
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), dpi=150)
    for ax, scale in zip(axes, SCALES):
        s  = summ[summ['scale'] == scale]
        hc = s[s['algorithm'] == 'HC']['mean'].iloc[0]
        ax.axhline(hc, color=INK_2, linestyle='--', linewidth=1.2)
        ax.text(1.0, hc, ' HC', transform=ax.get_yaxis_transform(),
                va='center', ha='left', fontsize=8.5, color=INK_2)
        for variant in VARIANTS:
            v  = s[s['algorithm'] == variant].copy()
            v['lc'] = v['lc'].astype(int)
            v  = v.sort_values('lc')
            ax.plot(v['lc'], v['mean'], color=COLOURS[variant], linewidth=2,
                    marker=MARKERS[variant], markersize=6, label=variant,
                    markeredgecolor=SURFACE, markeredgewidth=1.2)
        ax.set_xscale('log')
        ax.set_xticks([15, 50, 100, 500, 1000, 2500])
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        ax.set_title(scale.capitalize(), loc='left', color=INK)
        ax.set_xlabel('Step counter limit Lc (log scale)')
        ax.yaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0].set_ylabel('Mean final penalty (lower is better)')
    axes[0].legend(frameon=False, loc='upper right', fontsize=8.5)
    fig.suptitle('SCHC-imp is best at small Lc (15 to 25) at every scale, '
                 'while SCHC-all and SCHC-acp need Lc of 1500 to 2500',
                 x=0.01, ha='left', color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'lc_sensitivity.png', facecolor=SURFACE)
    plt.close(fig)


if __name__ == '__main__':
    improvement_figure()
    lc_sensitivity_figure()
    print(f"Figures written to {FIG_DIR}")
