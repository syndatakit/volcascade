"""Vol-timing: simpler version to avoid OOM.

Just compute the predictive regression and a basic long/short vol
strategy. No fancy vol-targeting.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps
from scipy.stats import theilslopes

ROOT = Path("/opt/data/volcascade")
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore
from volcascade.io import load_prices

prices = load_prices(["SPY", "XLE", "XLF"], start="2010-01-01", end="2024-12-31")
returns = np.log(prices / prices.shift(1)).dropna()
print(f"loaded {returns.shape}")

INNER_WINDOW = 10
ZSCORE_LOOKBACK = 120
FORWARD_DAYS = 5
TRADING_DAYS = 252

for asset in returns.columns:
    rets = returns[asset].dropna()
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=INNER_WINDOW)
    z = zscore(cascade, lookback=ZSCORE_LOOKBACK)
    sample = z[1]
    if isinstance(sample, pd.DataFrame):
        z_s = {k: z[k][asset] for k in [1, 2, 3, 4]}
    else:
        z_s = dict(z)
    s = slope(z_s)

    # Forward realized vol (annualized)
    fwd_vol = pd.Series(np.nan, index=rets.index)
    rets_arr = rets.values
    for i in range(len(rets) - FORWARD_DAYS):
        fwd_vol.iloc[i] = np.std(rets_arr[i + 1:i + 1 + FORWARD_DAYS]) * np.sqrt(TRADING_DAYS)

    valid = s.notna() & fwd_vol.notna()
    if valid.sum() < 100:
        print(f"{asset}: insufficient")
        continue
    s_v = s[valid].values
    f_v = fwd_vol[valid].values

    # Theil-Sen fit: fwd_vol = a + b * slope
    slope_fit, intercept_fit, _, _ = theilslopes(f_v, s_v)
    pred_vol = np.clip(intercept_fit + slope_fit * s.values, 0.05, 1.0)
    pred_vol = pd.Series(pred_vol, index=s.index)

    # Strategy: at each day, predict fwd_vol. If predicted > target, reduce vol
    # exposure. Position = vol_target / predicted_vol (capped 0.2-2.0).
    VOL_TARGET = 0.15
    valid_idx = pred_vol.notna() & fwd_vol.notna() & rets.notna()
    v = pred_vol[valid_idx].values
    f = fwd_vol[valid_idx].values
    r = rets[valid_idx].values
    pos = np.clip(VOL_TARGET / v, 0.2, 2.0)

    # Strategy daily return: position_t * r_{t+1}
    pos_shifted = pos[:-1]
    r_next = r[1:]
    strat_r = pos_shifted * r_next

    # Constant-target benchmark: position = vol_target / fwd_vol
    const_pos = np.clip(VOL_TARGET / f, 0.2, 2.0)[:-1]
    const_r = const_pos * r_next

    # Buy-and-hold: r_{t+1}
    bh_r = r_next

    def sharpe(x):
        if x.std() == 0:
            return 0.0
        return float(x.mean() / x.std() * np.sqrt(TRADING_DAYS))

    sharpe_strat = sharpe(strat_r)
    sharpe_const = sharpe(const_r)
    sharpe_bh = sharpe(bh_r)

    # Spearman of pred vs actual
    rho, _ = sps.spearmanr(v, f)
    print(f"\n{asset}:")
    print(f"  Spearman(predicted_vol, actual_fwd_vol): {rho:+.4f}")
    print(f"  Sharpe cascade-informed: {sharpe_strat:.3f}  (annualized)")
    print(f"  Sharpe constant-target (perfect): {sharpe_const:.3f}")
    print(f"  Sharpe buy-and-hold: {sharpe_bh:.3f}")
    diff = sharpe_strat - sharpe_bh
    sign = "BEATS" if diff > 0 else "LOSES"
    print(f"  --> cascade strategy {sign} B&H by {abs(diff):.3f}")
