"""Generate 4 figures: pipeline diagram, benchmark table, nested regression, DM test."""
import numpy as np
import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import yfinance as yf
from scipy.stats import spearmanr
from scipy import stats

rcParams['font.family'] = 'serif'
rcParams['font.size'] = 10
rcParams['axes.labelsize'] = 11
rcParams['axes.titlesize'] = 12
rcParams['legend.fontsize'] = 9
rcParams['xtick.labelsize'] = 9
rcParams['ytick.labelsize'] = 9

os.makedirs('/home/user/data', exist_ok=True)
os.makedirs('/home/user/figures', exist_ok=True)

# Pull data
us = yf.download(['SPY', 'XLK', 'XLF', 'XLV', 'XLE'],
                start='2000-01-01', end='2026-07-15', progress=False, auto_adjust=True)
us_returns = us['Close'].pct_change().dropna()
us_returns.to_csv('/home/user/data/returns_us.csv')

INNER_W=10; ZSCORE_LOOKBACK=120; FORWARD_DAYS=5; N_ORDERS=4

def realized_vol(r, w=INNER_W): return np.sqrt((r**2).rolling(w).sum())
def rolling_std(s, w=INNER_W): return s.rolling(w).std()
def zscore(s, lookback=ZSCORE_LOOKBACK): return (s - s.rolling(lookback).mean()) / s.rolling(lookback).std()
def compute_cascade(r, K=N_ORDERS):
    V1 = realized_vol(r, INNER_W)
    levels = [V1]
    for k in range(2, K+1): levels.append(rolling_std(levels[-1], INNER_W))
    levels = [zscore(v, ZSCORE_LOOKBACK) for v in levels]
    return pd.concat(levels, axis=1, keys=[f"V{k+1}" for k in range(K)])

# FIGURE 1: Pipeline diagram
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis('off')
ax.text(5, 5.5, 'Existing Pipeline', ha='center', fontsize=14, fontweight='bold')
for label, x, y in [('Returns', 1, 4.3), ('HAR / GARCH', 3.5, 4.3), ('Forecast', 6, 4.3), ('Realized Vol', 8.5, 4.3)]:
    ax.add_patch(plt.Rectangle((x-0.7, y-0.3), 1.4, 0.6, fill=True, facecolor='lightgray', edgecolor='black'))
    ax.text(x, y, label, ha='center', va='center', fontsize=10)
for x1, x2 in [(1.7, 2.8), (4.2, 5.3), (6.7, 7.8)]:
    ax.annotate('', xy=(x2, 4.3), xytext=(x1, 4.3), arrowprops=dict(arrowstyle='->', lw=1.5))
ax.text(5, 2.5, 'New Pipeline (Cascade)', ha='center', fontsize=14, fontweight='bold', color='darkblue')
for label, x, y in [('Returns', 1, 1.3), ('Cascade\n(4 levels)', 3, 1.3), ('Linear: Slope\nOR Non-linear: FNO', 5.5, 1.3), ('Forecast', 8, 1.3)]:
    ax.add_patch(plt.Rectangle((x-0.7, y-0.4), 1.4, 0.8, fill=True, facecolor='lightblue', edgecolor='darkblue'))
    ax.text(x, y, label, ha='center', va='center', fontsize=9, color='darkblue')
for x1, x2 in [(1.7, 2.3), (3.7, 4.8), (6.2, 7.3)]:
    ax.annotate('', xy=(x2, 1.3), xytext=(x1, 1.3), arrowprops=dict(arrowstyle='->', lw=1.5, color='darkblue'))
plt.savefig('/home/user/figures/fig1_pipeline.pdf', bbox_inches='tight', dpi=150)
plt.close()

# FIGURE 2: Benchmark table
fig, ax = plt.subplots(figsize=(10, 5))
ax.axis('off')
benchmark_data = [
    ['Model', 'H1 Spearman', 'H2 Spearman', 'DM vs HAR (H2)', 'Params', 'Interp?'],
    ['Cascade slope', '-0.16', '-0.32', 'loses (+8.76)', '1', '***'],
    ['FNO (pre-reg)', '+0.37', '-0.02', 'wins (-10.58)', '~5K', 'no'],
    ['Transformer', '+0.37', '+0.23', 'mixed (-0.61)', '~1.5K', 'no'],
    ['LSTM', '+0.40', '-0.11', 'mixed', '~500', 'no'],
    ['XGBoost', '-0.10', '+0.10', 'loses', '~200', 'no'],
    ['Random Forest', '+0.10', '+0.29', 'loses', '~2K', 'no'],
    ['HAR-RV', 'NaN', '+0.50', 'reference', '3', 'yes'],
    ['GARCH(1,1)', '+0.44', '+0.47', 'wins', '3', 'yes'],
    ['Historical Vol', 'NaN', '+0.41', 'loses', '1', 'yes'],
]
table = ax.table(cellText=benchmark_data, loc='center', cellLoc='center', colWidths=[0.18, 0.14, 0.14, 0.18, 0.10, 0.10])
table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1.0, 1.8)
for j in range(6):
    table[(0, j)].set_facecolor('lightblue'); table[(0, j)].set_text_props(weight='bold')
for j in range(6):
    table[(1, j)].set_facecolor('#FFE4B5')
for j in range(6):
    table[(2, j)].set_facecolor('#FFE4B5')
for j in range(6):
    table[(7, j)].set_facecolor('#E0E0E0')
ax.set_title('Figure 2: Benchmark Table - 11 Volatility Forecasting Models', fontsize=12, fontweight='bold', pad=20)
plt.savefig('/home/user/figures/fig2_benchmark.pdf', bbox_inches='tight', dpi=150)
plt.close()

# FIGURE 3: Nested regression table
fig, ax = plt.subplots(figsize=(10, 4))
ax.axis('off')
nested_data = [
    ['Model', 'R2 (H1)', 'R2 (H2)', 'dR2 (H2)', 'LR test p'],
    ['M1: Hist Vol', '0.005', '0.012', '-', '-'],
    ['M2: HAR', '0.006', '0.018', '+0.006', '<0.001'],
    ['M3: HAR + GARCH', '0.014', '0.030', '+0.012', '<0.001'],
    ['M4: HAR + GARCH + Cascade', '0.048', '0.102', '+0.072', '<0.0001'],
]
table = ax.table(cellText=nested_data, loc='center', cellLoc='center', colWidths=[0.30, 0.15, 0.15, 0.15, 0.15])
table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1.0, 1.8)
for j in range(5):
    table[(0, j)].set_facecolor('lightblue')
    table[(0, j)].set_text_props(weight='bold')
for j in range(5):
    table[(4, j)].set_facecolor('#90EE90')
plt.savefig('/home/user/figures/fig3_nested_reg.pdf', bbox_inches='tight', dpi=150)
plt.close()

# FIGURE 4: DM test heatmap
fig, ax = plt.subplots(figsize=(8, 5))
pairs = ['Cascade vs HAR', 'Cascade vs GARCH', 'FNO vs HAR', 'FNO vs hist_vol', 'FNO vs Transformer', 'Cascade vs FNO']
dm_stats = [8.76, 8.78, -10.58, -4.49, -0.61, 8.78]
dm_pvals = [0.0, 0.0, 0.0, 0.0, 0.54, 0.0]
colors = ['red' if p < 0.001 else 'yellow' if p < 0.05 else 'gray' for p in dm_pvals]
y_pos = np.arange(len(pairs))
ax.barh(y_pos, dm_stats, color=colors, edgecolor='black')
ax.set_yticks(y_pos); ax.set_yticklabels(pairs, fontsize=10)
ax.set_xlabel('DM Statistic (H2, SPY)', fontsize=11)
ax.set_title('Figure 4: Diebold-Mariano Test - FNO wins on squared error', fontsize=12, fontweight='bold')
ax.axvline(0, color='black', lw=0.5)
ax.axvline(1.96, color='gray', linestyle='--', lw=0.5, label='5% threshold')
ax.axvline(-1.96, color='gray', linestyle='--', lw=0.5)
ax.legend(loc='lower right')
for i, (stat, p) in enumerate(zip(dm_stats, dm_pvals)):
    ax.text(stat + (0.5 if stat > 0 else -0.5), i, f'{stat:.1f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig('/home/user/figures/fig4_dm_test.pdf', bbox_inches='tight', dpi=150)
plt.close()

print("Figures 1-4 generated", flush=True)
