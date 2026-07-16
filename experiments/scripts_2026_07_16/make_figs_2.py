"""Generate 4 more figures: calibration, FNO explain, rolling, strategy."""
import numpy as np
import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

us_returns = pd.read_csv('/home/user/data/returns_us.csv', index_col=0, parse_dates=True)
INNER_W=10; ZSCORE_LOOKBACK=120; FORWARD_DAYS=5; N_ORDERS=4
os.makedirs('/home/user/figures', exist_ok=True)

def realized_vol(r, w=INNER_W): return np.sqrt((r**2).rolling(w).sum())
def rolling_std(s, w=INNER_W): return s.rolling(w).std()
def zscore(s, lookback=ZSCORE_LOOKBACK): return (s - s.rolling(lookback).mean()) / s.rolling(lookback).std()
def compute_cascade(r, K=N_ORDERS):
    V1 = realized_vol(r, INNER_W)
    levels = [V1]
    for k in range(2, K+1): levels.append(rolling_std(levels[-1], INNER_W))
    levels = [zscore(v, ZSCORE_LOOKBACK) for v in levels]
    return pd.concat(levels, axis=1, keys=[f"V{k+1}" for k in range(K)])

# FIGURE 5: Calibration
fig, ax = plt.subplots(figsize=(7, 6))
r = us_returns['SPY']
fwd = np.sqrt((r**2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
cascade = compute_cascade(r)
slopes = []; dates = []
for d in cascade.index:
    z = cascade.loc[d].values
    if np.any(np.isnan(z)): continue
    if d not in fwd.index or np.isnan(fwd.loc[d]): continue
    k = np.arange(1, 5); km = k.mean(); zm = z.mean()
    s = np.sum((k-km)*(z-zm))/np.sum((k-km)**2)
    slopes.append(s); dates.append(d)
pred = pd.Series(slopes, index=dates)
common = pred.index.intersection(fwd.index)
test = (common >= pd.Timestamp('2025-01-01')) & (common <= pd.Timestamp('2026-07-15'))
p = -pred.loc[common][test].values
a = fwd.loc[common][test].values
ax.scatter(p, a, alpha=0.4, s=15, color='blue', label='Data')
mx = max(p.max(), a.max())
ax.plot([0, mx], [0, mx], 'k--', lw=1, label='y=x')
rho = spearmanr(p, a)[0]
ax.set_xlabel('Predicted vol (cascade slope, negated)', fontsize=11)
ax.set_ylabel('Realized 5-day vol', fontsize=11)
ax.set_title(f'Figure 5: Calibration plot (SPY, 2025+, rho = {rho:.3f})', fontsize=12, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig('/home/user/figures/fig5_calibration.pdf', bbox_inches='tight', dpi=150)
plt.close()

# FIGURE 6: FNO explainability
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
modes = ['Mode 0\n(lowest freq)', 'Mode 1', 'Mode 2', 'Mode 3']
importance_modes = [0.231, -0.054, -0.011, -0.002]
colors_m = ['darkred' if x > 0.1 else 'lightgray' for x in importance_modes]
axes[0].bar(modes, importance_modes, color=colors_m, edgecolor='black')
axes[0].set_ylabel('Importance (Spearman drop)', fontsize=11)
axes[0].set_title('Fourier Mode Importance', fontsize=12, fontweight='bold')
axes[0].axhline(0, color='black', lw=0.5)
features = ['V1 (realized vol)', 'V2 (rolling std)', 'V3 (rolling std)', 'V4 (rolling std)']
importance_f = [0.068, -0.037, -0.017, -0.021]
colors_f = ['darkred' if x > 0.05 else 'lightgray' for x in importance_f]
axes[1].bar(features, importance_f, color=colors_f, edgecolor='black')
axes[1].set_ylabel('Importance (Spearman drop)', fontsize=11)
axes[1].set_title('Cascade Level Importance', fontsize=12, fontweight='bold')
axes[1].axhline(0, color='black', lw=0.5)
plt.tight_layout()
plt.savefig('/home/user/figures/fig6_fno_explain.pdf', bbox_inches='tight', dpi=150)
plt.close()

# FIGURE 7: Rolling stability
fig, ax = plt.subplots(figsize=(10, 5))
US_TICKERS = ['SPY', 'XLK', 'XLF', 'XLV', 'XLE']
colors_t = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
for ticker, c in zip(US_TICKERS, colors_t):
    r = us_returns[ticker]
    fwd = np.sqrt((r**2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    cascade = compute_cascade(r)
    slopes = []; dates = []
    for d in cascade.index:
        z = cascade.loc[d].values
        if np.any(np.isnan(z)): continue
        if d not in fwd.index or np.isnan(fwd.loc[d]): continue
        k = np.arange(1, 5); km = k.mean(); zm = z.mean()
        s = np.sum((k-km)*(z-zm))/np.sum((k-km)**2)
        slopes.append(s); dates.append(d)
    pred = pd.Series(slopes, index=dates)
    common = pred.index.intersection(fwd.index)
    pred, f = pred.loc[common], fwd.loc[common]
    rolling_spearman = []
    years = []
    for year in range(2003, 2025):
        window_start = pd.Timestamp(f'{year}-01-01')
        window_end = pd.Timestamp(f'{year+2}-12-31')
        in_window = (pred.index >= window_start) & (pred.index <= window_end)
        if in_window.sum() < 100: continue
        sp = spearmanr(pred[in_window], f[in_window])[0]
        rolling_spearman.append(sp); years.append(year)
    ax.plot(years, rolling_spearman, marker='o', label=ticker, color=c, lw=1.5)
ax.axhline(0, color='black', lw=0.5, linestyle='--')
ax.set_xlabel('Start year of 3-year window', fontsize=11)
ax.set_ylabel('Spearman correlation', fontsize=11)
ax.set_title('Figure 7: Rolling 3-year Spearman stability (2003-2024)', fontsize=12, fontweight='bold')
ax.legend(loc='lower left', ncol=5)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('/home/user/figures/fig7_rolling.pdf', bbox_inches='tight', dpi=150)
plt.close()

# FIGURE 8: Strategy
fig, ax = plt.subplots(figsize=(9, 5))
assets = ['SPY', 'XLK', 'XLF', 'XLV', 'XLE']
sharpe_cascade = [3.21, 2.91, 1.71, 1.09, 1.57]
sharpe_bh = [1.08, 1.20, 0.73, 0.89, 0.89]
x = np.arange(len(assets))
width = 0.35
ax.bar(x - width/2, sharpe_cascade, width, label='Cascade vol-targeting', color='darkblue', edgecolor='black')
ax.bar(x + width/2, sharpe_bh, width, label='Buy-and-hold', color='lightgray', edgecolor='black')
ax.set_xticks(x); ax.set_xticklabels(assets)
ax.set_ylabel('Sharpe ratio', fontsize=11)
ax.set_title('Figure 8: Vol-targeting strategy (2025+, oracle)', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3, axis='y')
for i, (c, b) in enumerate(zip(sharpe_cascade, sharpe_bh)):
    ax.text(i - width/2, c + 0.1, f'{c:.2f}', ha='center', fontsize=9)
    ax.text(i + width/2, b + 0.1, f'{b:.2f}', ha='center', fontsize=9)
plt.tight_layout()
plt.savefig('/home/user/figures/fig8_strategy.pdf', bbox_inches='tight', dpi=150)
plt.close()

print("Figures 5-8 generated", flush=True)
