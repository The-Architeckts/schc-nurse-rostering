'''
Generate figures for dissertation poster using sprint and medium05 data.

Required CSV files:
- outputs/sprint_lc_sweep_YYYYMMDD_HHMMSS/summary.csv (sprint results)
- outputs/medium_lc_scaling_YYYYMMDD_HHMMSS/detailed_results.csv (medium05 partial)

Generates 4 poster-ready figures:
1. Sprint + Medium Lc sensitivity (line graph, all 3 variants, both scales)
2. SCHC-acp: Sprint vs. Medium05 (bar chart showing Lc sensitivity emergence)
3. Cost-benefit tradeoff (scatter: quality vs. runtime, with min/max labels)
4. Overall performance comparison (bar chart: HC vs. optimal SCHC, worst-to-best)

v2 changes:
- Figure 1: Medium instance overlay added to tie scales together
- Figure 3: Lc point annotations removed; min/max penalty shown instead
- Figure 4: Bars ordered worst-to-best; improvement labels use minus sign
- All output filenames prefixed with 01_, 02_, etc. to avoid overwriting v1 outputs
'''

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

# Set POSTER-quality defaults (readable from 2-3 meters)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.transparent'] = True
plt.rcParams['font.size'] = 18
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.labelsize'] = 22
plt.rcParams['axes.titlesize'] = 26
plt.rcParams['legend.fontsize'] = 18
plt.rcParams['xtick.labelsize'] = 18
plt.rcParams['ytick.labelsize'] = 18
plt.rcParams['lines.linewidth'] = 3.5
plt.rcParams['lines.markersize'] = 10

# Color scheme (colorblind-friendly)
COLORS = {
    'all': '#0173B2',   # Blue
    'acp': '#DE8F05',   # Orange
    'imp': '#029E73',   # Green
    'HC':  '#CC78BC'    # Purple
}

# ============================================================================
# DATA LOADING
# ============================================================================

def load_sprint_data(csv_path):
    df = pd.read_csv(csv_path)
    return df

def load_medium_data(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df[df['instance'] == 'INRC1_medium05']
        return df
    except (FileNotFoundError, TypeError):
        print("  Medium CSV not found, using manual data from terminal output...")
        return create_manual_medium_data()

def create_manual_medium_data():
    '''Manually extracted medium05 data from terminal output.'''
    data = []

    hc_results = [359, 356, 348, 358, 354, 365, 363, 352, 356, 369]
    for i, penalty in enumerate(hc_results):
        data.append({
            'instance': 'INRC1_medium05', 'algorithm': 'HC', 'variant': 'HC',
            'Lc': 0, 'run': i + 1, 'baseline': 549, 'final': penalty,
            'improvement_pct': ((549 - penalty) / 549) * 100,
            'bound_updates': 0, 'time': 31.0
        })

    schc_all_500 = [
        (328, 228, 237.6), (335, 197, 180.3), (327, 218, 198.2),
        (320, 287, 257.3), (327, 232, 209.8), (325, 259, 226.7),
        (320, 222, 189.8), (325, 240, 207.5), (327, 265, 225.2),
        (327, 221, 188.7)
    ]
    for i, (penalty, updates, time) in enumerate(schc_all_500):
        data.append({
            'instance': 'INRC1_medium05', 'algorithm': 'SCHC', 'variant': 'all',
            'Lc': 500, 'run': i + 1, 'baseline': 549, 'final': penalty,
            'improvement_pct': ((549 - penalty) / 549) * 100,
            'bound_updates': updates, 'time': time
        })

    schc_all_1500 = [
        (315, 198, 514.1), (317, 197, 510.9), (317, 183, 474.3),
        (321, 192, 496.0), (328, 186, 487.1), (317, 201, 523.3),
        (319, 189, 491.1), (327, 190, 495.3), (322, 193, 503.5),
        (323, 183, 475.1)
    ]
    for i, (penalty, updates, time) in enumerate(schc_all_1500):
        data.append({
            'instance': 'INRC1_medium05', 'algorithm': 'SCHC', 'variant': 'all',
            'Lc': 1500, 'run': i + 1, 'baseline': 549, 'final': penalty,
            'improvement_pct': ((549 - penalty) / 549) * 100,
            'bound_updates': updates, 'time': time
        })

    schc_all_5000 = [
        (318, 196, 1692.9), (319, 175, 1510.2), (316, 187, 1613.5),
        (311, 189, 1630.4), (313, 186, 1603.2), (312, 189, 1628.9),
        (315, 187, 1618.2), (317, 183, 1586.3), (314, 186, 1602.9),
        (318, 181, 1570.2)
    ]
    for i, (penalty, updates, time) in enumerate(schc_all_5000):
        data.append({
            'instance': 'INRC1_medium05', 'algorithm': 'SCHC', 'variant': 'all',
            'Lc': 5000, 'run': i + 1, 'baseline': 549, 'final': penalty,
            'improvement_pct': ((549 - penalty) / 549) * 100,
            'bound_updates': updates, 'time': time
        })

    schc_acp_500 = [
        (313, 170, 471.7), (312, 177, 454.0), (318, 174, 465.1),
        (321, 175, 425.8), (320, 166, 415.6), (322, 169, 408.0),
        (319, 168, 450.7), (315, 170, 462.5), (320, 168, 415.3),
        (320, 173, 425.5)
    ]
    for i, (penalty, updates, time) in enumerate(schc_acp_500):
        data.append({
            'instance': 'INRC1_medium05', 'algorithm': 'SCHC', 'variant': 'acp',
            'Lc': 500, 'run': i + 1, 'baseline': 549, 'final': penalty,
            'improvement_pct': ((549 - penalty) / 549) * 100,
            'bound_updates': updates, 'time': time
        })

    schc_acp_1500 = [
        (314, 175, 1232.1), (310, 177, 1263.5), (310, 187, 1310.7),
        (313, 175, 1211.9), (313, 168, 1201.9), (316, 159, 1112.2),
        (317, 171, 1180.4), (314, 174, 1237.5), (316, 180, 1252.7),
        (311, 181, 1285.4)
    ]
    for i, (penalty, updates, time) in enumerate(schc_acp_1500):
        data.append({
            'instance': 'INRC1_medium05', 'algorithm': 'SCHC', 'variant': 'acp',
            'Lc': 1500, 'run': i + 1, 'baseline': 549, 'final': penalty,
            'improvement_pct': ((549 - penalty) / 549) * 100,
            'bound_updates': updates, 'time': time
        })

    schc_acp_5000 = [
        (310, 179, 3963.6), (313, 172, 3780.8), (312, 158, 3497.7),
        (308, 165, 3675.4), (314, 170, 3671.9), (317, 168, 3611.6),
        (313, 157, 3483.4)
    ]
    for i, (penalty, updates, time) in enumerate(schc_acp_5000):
        data.append({
            'instance': 'INRC1_medium05', 'algorithm': 'SCHC', 'variant': 'acp',
            'Lc': 5000, 'run': i + 1, 'baseline': 549, 'final': penalty,
            'improvement_pct': ((549 - penalty) / 549) * 100,
            'bound_updates': updates, 'time': time
        })

    return pd.DataFrame(data)


# ============================================================================
# FIGURE 1: Sprint + Medium Lc Sensitivity (Line Graph, dual axes)
# ============================================================================

def create_sprint_lc_sensitivity(sprint_df, medium_df, output_path):
    '''
    Two-panel figure: sprint (left) and medium (right), same variant colours,
    so the reader can see how Lc sensitivity changes with scale.
    The medium panel uses only the Lc values available in medium_df.
    '''
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

    sprint_schc = sprint_df[sprint_df['Algorithm'] != 'HC']
    medium_schc = medium_df[
        (medium_df['algorithm'] == 'SCHC') &
        (medium_df['variant'].isin(['all', 'acp', 'imp']))
    ]

    for variant in ['all', 'acp', 'imp']:
        # Sprint
        vdata = sprint_schc[sprint_schc['Algorithm'] == f'SCHC-{variant}']
        grouped = vdata.groupby('Lc')['Final'].mean().sort_index()
        ax1.plot(grouped.index.values, grouped.values,
                 marker='o', linewidth=4, markersize=12,
                 color=COLORS[variant], label=f'SCHC-{variant}', alpha=0.9)

        # Medium
        vdata_m = medium_schc[medium_schc['variant'] == variant]
        if not vdata_m.empty:
            grouped_m = vdata_m.groupby('Lc')['final'].mean().sort_index()
            ax2.plot(grouped_m.index.values, grouped_m.values,
                     marker='o', linewidth=4, markersize=12,
                     color=COLORS[variant], label=f'SCHC-{variant}', alpha=0.9)

    # HC baselines
    hc_sprint = sprint_df[sprint_df['Algorithm'] == 'HC']['Final'].mean()
    ax1.axhline(hc_sprint, color=COLORS['HC'], linestyle='--',
                linewidth=3.5, label='HC baseline', alpha=0.8)

    hc_medium = medium_df[medium_df['algorithm'] == 'HC']['final'].mean()
    ax2.axhline(hc_medium, color=COLORS['HC'], linestyle='--',
                linewidth=3.5, label='HC baseline', alpha=0.8)

    for ax, title in zip([ax1, ax2],
                         ['Sprint Instances (n ≈ 280)', 'Medium Instances (n ≈ 1,400)']):
        ax.set_xlabel('Lc (Step Counter Limit)', fontweight='bold', fontsize=24)
        ax.set_ylabel('Average Penalty', fontweight='bold', fontsize=24)
        ax.set_title(title, fontweight='bold', fontsize=26, pad=15)
        ax.grid(True, alpha=0.25, linestyle=':', linewidth=1.5)
        ax.legend(loc='upper right', framealpha=0.95, fontsize=18)
        ax.tick_params(axis='both', which='major', labelsize=20, width=2, length=6)

    fig.suptitle('Lc Sensitivity Across Problem Scales',
                 fontweight='bold', fontsize=30, y=1.02)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# FIGURE 2: SCHC-acp Lc Sensitivity Emergence (Bar Chart)
# ============================================================================

def create_schc_acp_comparison(sprint_df, medium_df, output_path):
    '''Side-by-side comparison showing scale-dependent SCHC-acp behaviour.'''
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), sharey=False)

    sprint_acp = sprint_df[sprint_df['Algorithm'] == 'SCHC-acp']
    sprint_grouped = sprint_acp.groupby('Lc')['Final'].agg(['mean', 'std'])

    medium_acp = medium_df[(medium_df['algorithm'] == 'SCHC') &
                           (medium_df['variant'] == 'acp')]
    medium_grouped = medium_acp.groupby('Lc')['final'].agg(['mean', 'std'])

    def _draw_bars(ax, grouped, title):
        lc_vals = grouped.index.values
        means = grouped['mean'].values
        stds = grouped['std'].values
        bars = ax.bar(range(len(lc_vals)), means,
                      color=COLORS['acp'], alpha=0.85, yerr=stds,
                      capsize=6, edgecolor='black', linewidth=2)
        ax.set_xticks(range(len(lc_vals)))
        ax.set_xticklabels(lc_vals, fontsize=20)
        ax.set_xlabel('Lc Value', fontweight='bold', fontsize=24)
        ax.set_ylabel('Average Penalty', fontweight='bold', fontsize=24)
        ax.set_title(title, fontweight='bold', fontsize=26, pad=15)
        ax.grid(True, alpha=0.25, axis='y', linestyle=':', linewidth=1.5)
        ax.tick_params(axis='both', which='major', labelsize=20, width=2, length=6)
        for bar, val, std in zip(bars, means, stds):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + std + 1.5,
                    f'{val:.1f}', ha='center', va='bottom',
                    fontsize=18, fontweight='bold')

    _draw_bars(ax1, sprint_grouped, 'Sprint (n=280)\nLc-Insensitive')
    _draw_bars(ax2, medium_grouped, 'Medium (n=1,400)\nLc-Sensitive')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# FIGURE 3: Cost-Benefit Tradeoff (Scatter, min/max labels)
# ============================================================================

def create_cost_benefit_tradeoff(medium_df, output_path):
    '''
    Scatter of quality vs. runtime for SCHC-all across Lc values.
    Each point is the mean; error bars show std.
    Min and max observed penalties are labelled near the point instead
    of repeating the Lc value (already in the legend).
    '''
    fig, ax = plt.subplots(figsize=(10, 7))

    schc_all = medium_df[
        (medium_df['algorithm'] == 'SCHC') &
        (medium_df['variant'] == 'all')
    ]

    lc_colors = {500: '#0173B2', 1500: '#DE8F05', 5000: '#CC78BC'}

    for lc, group in schc_all.groupby('Lc'):
        mean_penalty = group['final'].mean()
        mean_time    = group['time'].mean()
        std_penalty  = group['final'].std()
        std_time     = group['time'].std()
        min_penalty  = group['final'].min()
        max_penalty  = group['final'].max()

        ax.errorbar(mean_time, mean_penalty,
                    xerr=std_time, yerr=std_penalty,
                    marker='o', markersize=20, capsize=8,
                    linewidth=3.5, color=lc_colors[lc],
                    label=f'Lc={lc}', alpha=0.9)

        # Min label (below the lower error bar)
        ax.annotate(f'min={min_penalty}',
                    xy=(mean_time, mean_penalty - std_penalty),
                    xytext=(0, -28), textcoords='offset points',
                    ha='center', va='top',
                    fontsize=16, fontweight='bold', color=lc_colors[lc],
                    bbox=dict(boxstyle='round,pad=0.3',
                              facecolor='white', alpha=0.8,
                              edgecolor=lc_colors[lc], linewidth=1.5))

        # Max label (above the upper error bar)
        ax.annotate(f'max={max_penalty}',
                    xy=(mean_time, mean_penalty + std_penalty),
                    xytext=(0, 28), textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=16, fontweight='bold', color=lc_colors[lc],
                    bbox=dict(boxstyle='round,pad=0.3',
                              facecolor='white', alpha=0.8,
                              edgecolor=lc_colors[lc], linewidth=1.5))

    ax.set_xlabel('Runtime (seconds)', fontweight='bold', fontsize=24)
    ax.set_ylabel('Average Penalty', fontweight='bold', fontsize=24)
    ax.set_title('Medium: Quality vs. Cost (SCHC-all)',
                 fontweight='bold', fontsize=28, pad=20)
    ax.grid(True, alpha=0.25, linestyle=':', linewidth=1.5)
    ax.legend(loc='upper right', fontsize=20, framealpha=0.95)
    ax.tick_params(axis='both', which='major', labelsize=20, width=2, length=6)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# FIGURE 4: Overall Performance Comparison (worst to best, minus labels)
# ============================================================================

def create_overall_comparison(sprint_df, output_path):
    '''
    Bar chart of HC vs. optimal-Lc SCHC variants on sprint instances.
    Bars ordered worst (highest penalty) to best (lowest penalty).
    Improvement labels use a minus sign to indicate penalty reduction.
    '''
    fig, ax = plt.subplots(figsize=(11, 7))

    hc_mean = sprint_df[sprint_df['Algorithm'] == 'HC']['Final'].mean()
    hc_std  = sprint_df[sprint_df['Algorithm'] == 'HC']['Final'].std()

    optimal_lc = {'all': 1000, 'acp': 100, 'imp': 1000}

    entries = [('HC', hc_mean, hc_std, COLORS['HC'])]
    for variant in ['all', 'acp', 'imp']:
        lc = optimal_lc[variant]
        vdata = sprint_df[
            (sprint_df['Algorithm'] == f'SCHC-{variant}') &
            (sprint_df['Lc'] == lc)
        ]
        entries.append((
            f'SCHC-{variant}',
            vdata['Final'].mean(),
            vdata['Final'].std(),
            COLORS[variant]
        ))

    # Sort worst (highest mean penalty) to best (lowest)
    entries.sort(key=lambda e: e[1], reverse=True)

    labels      = [e[0] for e in entries]
    means       = [e[1] for e in entries]
    stds        = [e[2] for e in entries]
    colors_list = [e[3] for e in entries]

    x = np.arange(len(labels))
    bars = ax.bar(x, means, yerr=stds, capsize=8, width=0.7,
                  color=colors_list, alpha=0.85,
                  edgecolor='black', linewidth=2.5)

    for i, (bar, mean, std, label) in enumerate(zip(bars, means, stds, labels)):
        # Mean value above bar
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + std + 1,
                f'{mean:.1f}', ha='center', va='bottom',
                fontsize=20, fontweight='bold')

        # Improvement badge (only for SCHC algorithms)
        if label != 'HC':
            improvement = ((hc_mean - mean) / hc_mean) * 100
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() / 2,
                    f'-{improvement:.1f}%',
                    ha='center', va='center',
                    fontsize=18, fontweight='bold', color='white',
                    bbox=dict(boxstyle='round,pad=0.4',
                              facecolor='darkgreen', alpha=0.9))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=20, fontweight='bold')
    ax.set_ylabel('Average Penalty', fontweight='bold', fontsize=24)
    ax.set_title('Algorithm Comparison (Sprint, Optimal Lc)',
                 fontweight='bold', fontsize=28, pad=20)
    ax.grid(True, alpha=0.25, axis='y', linestyle=':', linewidth=1.5)
    ax.tick_params(axis='both', which='major', labelsize=20, width=2, length=6)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()
    print(f"  Saved: {output_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("GENERATING POSTER FIGURES (v2)")
    print("=" * 80)
    print()

    outputs_dir = Path('outputs')

    # Sprint data (required)
    sprint_dirs = sorted(outputs_dir.glob('sprint_lc_sweep_*'))
    if not sprint_dirs:
        print("ERROR: No sprint data found in outputs/")
        print("Please run the sprint Lc sweep test first.")
        return
    sprint_csv = sprint_dirs[-1] / 'summary.csv'
    print(f"Loading sprint data:  {sprint_csv}")
    sprint_df = load_sprint_data(sprint_csv)
    print(f"  {len(sprint_df)} rows loaded")

    # Medium data (optional fallback)
    medium_dirs = sorted(outputs_dir.glob('medium_lc_scaling_*'))
    medium_csv = (medium_dirs[-1] / 'detailed_results.csv') if medium_dirs else None
    if medium_csv:
        print(f"Loading medium data:  {medium_csv}")
    else:
        print("  No medium test directory found, using manual data...")
    medium_df = load_medium_data(medium_csv)
    print(f"  {len(medium_df)} rows loaded (medium05 only)")
    print()

    # Output directory: timestamped so previous runs are never overwritten
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fig_dir = Path('poster_figures') / f"v2_{timestamp}"
    fig_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving figures to: {fig_dir}/")
    print()

    create_sprint_lc_sensitivity(
        sprint_df, medium_df,
        fig_dir / '01_sprint_medium_lc_sensitivity.png'
    )

    create_schc_acp_comparison(
        sprint_df, medium_df,
        fig_dir / '02_schc_acp_scale_behavior.png'
    )

    create_cost_benefit_tradeoff(
        medium_df,
        fig_dir / '03_cost_benefit_tradeoff.png'
    )

    create_overall_comparison(
        sprint_df,
        fig_dir / '04_overall_performance.png'
    )

    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print(f"\nAll figures saved to: {fig_dir}/")
    print("\nFigures generated:")
    print("  01_sprint_medium_lc_sensitivity.png  -- Lc sensitivity, sprint + medium")
    print("  02_schc_acp_scale_behavior.png       -- SCHC-acp scale-dependent behaviour")
    print("  03_cost_benefit_tradeoff.png         -- Quality vs. runtime (min/max labels)")
    print("  04_overall_performance.png           -- Algorithm comparison, worst-to-best")

if __name__ == '__main__':
    main()