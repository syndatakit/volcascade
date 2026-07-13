"""Practical application: vol-timing rule based on cascade slope.

If the cascade slope predicts forward vol (the vol-peak finding), a
practical use case is a vol-timing rule: use the cascade signal to
adjust vol exposure. This is the "killer use case" the paper needs.

The rule:
- Each day, compute the cascade slope β(t).
- Map β(t) to a position size: when slope is very negative (vol
  peaking → vol about to fall), reduce vol exposure. When slope is
  very positive (vol bottoming → vol about to rise), increase vol
  exposure.
- Compare the Sharpe ratio of this rule vs a constant-vol benchmark.

Specifically: daily realized vol is the proxy. We go long vol when
β is in the top quintile (steep cascade = vol will fall? NO — wait,
the sign). Let me re-derive.

We observed: high β (steepening) → forward vol is LOWER (Spearman
negative). So:
- High β → reduce vol exposure (vol will fall)
- Low β (or negative β) → increase vol exposure (vol will rise)

Position sizing: at each day, compute β(t) and use it to set the
position in a vol-targeting strategy. The position is inversely
proportional to the predicted vol: if we expect vol to fall, we
reduce vol exposure (the position is on realized vol).

Actually, simpler: the cascade signal is "predict forward vol". A
trader with a vol TARGET (e.g., 15% annualized) would scale
exposure based on predicted vol: if predicted vol > target, reduce
position; if predicted vol < target, increase position.

We measure: does the cascade-informed vol-targeting rule achieve
higher risk-adjusted returns than constant-target?
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore  # noqa: E402
from volcascade.io import SP500_SECTOR_ETFS, load_prices  # noqa: E402

RESULTS_DIR = ROOT / "results"
ASSETS = ["SPY", "XLE", "XLF", "XLV", "XLY"]


def main() -> None:
    print("=" * 78)
    print("PRACTICAL APPLICATION: cascade-informed vol-targeting")
    print("=" * 78)

    print(f"\nloading {ASSETS} (2000-2024)...")
    t0 = time.time()
    prices = load_prices(ASSETS, start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    # Pre-registered parameters (committed to before running the sweep)
    INNER_WINDOW = 10
    ZSCORE_LOOKBACK = 120
    FORWARD_DAYS = 5
    VOL_TARGET = 0.15  # 15% annualized target vol
    TRADING_DAYS = 252

    print("=" * 78)
    print(f"VOL-TIMING RULE")
    print(f"  inner_window = {INNER_WINDOW}")
    print(f"  zscore_lookback = {ZSCORE_LOOKBACK}")
    print(f"  forward_days = {FORWARD_DAYS}")
    print(f"  vol_target = {VOL_TARGET:.0%} annualized")
    print("=" * 78)

    for asset in ASSETS:
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
        for i in range(len(rets) - FORWARD_DAYS):
            fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + FORWARD_DAYS].std()) * np.sqrt(TRADING_DAYS)

        # Predicted vol: cascade signal-based estimate
        # We observed: Spearman(s, fwd_vol) = -0.10 to -0.20
        # Use the cascade slope to predict fwd_vol:
        #   predicted_vol = base + coef * slope
        # Fit on the relationship
        valid = s.notna() & fwd_vol.notna()
        if valid.sum() < 100:
            continue
        # Robust linear fit: fwd_vol = a + b * slope
        from scipy.stats import theilslopes
        slope_fit, intercept_fit, _, _ = theilslopes(fwd_vol[valid].to_numpy(),
                                                    s[valid].to_numpy())
        # Predicted vol
        pred_vol = intercept_fit + slope_fit * s
        # Clip to reasonable range
        pred_vol = pred_vol.clip(lower=0.05, upper=1.0)

        # Vol-targeting position: position = vol_target / pred_vol
        # (if predicted vol is 30% and target is 15%, we want half exposure)
        valid_idx = pred_vol.notna() & fwd_vol.notna() & rets.notna()
        v = pred_vol[valid_idx]
        f = fwd_vol[valid_idx]
        r = rets[valid_idx]

        # Position size
        pos = VOL_TARGET / v
        # Position is 0.5x to 2.0x typically
        # Daily strategy return: position * next-day return
        # We use forward 1-day return as the strategy P&L
        strat_r = pos.shift(1) * r

        # Constant-vol benchmark: position = vol_target / fwd_vol
        # (i.e., what we WOULD have done with perfect knowledge)
        const_pos = VOL_TARGET / f
        const_r = const_pos.shift(1) * r

        # Buy-and-hold: position = 1
        bh_r = r

        # Sharpe ratios (annualized)
        def sharpe(x):
            x = x.dropna()
            if len(x) < 50 or x.std() == 0:
                return np.nan
            return float(x.mean() / x.std() * np.sqrt(TRADING_DAYS))

        sharpe_strat = sharpe(strat_r)
        sharpe_const = sharpe(const_r)
        sharpe_bh = sharpe(bh_r)

        # Annualized returns
        ret_strat = (1 + strat_r).prod() ** (TRADING_DAYS / len(strat_r.dropna())) - 1
        ret_const = (1 + const_r).prod() ** (TRADING_DAYS / len(const_r.dropna())) - 1
        ret_bh = (1 + bh_r).prod() ** (TRADING_DAYS / len(bh_r.dropna())) - 1

        # Vol of strategy
        vol_strat = strat_r.std() * np.sqrt(TRADING_DAYS)

        # Spearman of predicted vs actual
        rho, p = sps.spearmanr(v.dropna(), f.dropna())

        print(f"\n  {asset}:")
        print(f"    Spearman(predicted_vol, fwd_vol): {rho:+.4f}  p={p:.2e}")
        print(f"    Sharpe (cascade-informed): {sharpe_strat:.3f}  (return={ret_strat:.2%}, vol={vol_strat:.2%})")
        print(f"    Sharpe (constant-target, perfect fwd_vol): {sharpe_const:.3f}  (return={ret_const:.2%})")
        print(f"    Sharpe (buy-and-hold): {sharpe_bh:.3f}  (return={ret_bh:.2%})")
        if sharpe_strat > sharpe_bh:
            print(f"    --> CASCADE STRATEGY BEATS B&H by {(sharpe_strat - sharpe_bh):.3f}")
        else:
            print(f"    --> cascade strategy underperforms B&H by {(sharpe_bh - sharpe_strat):.3f}")

    # Also test a simple LONG-VOL rule based on the cascade
    print("\n" + "=" * 78)
    print("SIMPLE LONG-VOL RULE: long vol when cascade is in bottom quintile (very negative)")
    print("=" * 78)
    for asset in ASSETS:
        rets = returns[asset].dropna()
        cascade = build(rets, orders=(1, 2, 3, 4), inner_window=INNER_WINDOW)
        z = zscore(cascade, lookback=ZSCORE_LOOKBACK)
        sample = z[1]
        if isinstance(sample, pd.DataFrame):
            z_s = {k: z[k][asset] for k in [1, 2, 3, 4]}
        else:
            z_s = dict(z)
        s = slope(z_s).dropna()

        # Bottom quintile = very negative slope = vol is peaking → vol about to fall
        # Long vol = buy realized vol
        # We need to backtest this with a vol instrument
        # For simplicity, use forward realized vol as the "vol asset"
        fwd_vol = pd.Series(np.nan, index=rets.index)
        for i in range(len(rets) - FORWARD_DAYS):
            fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + FORWARD_DAYS].std()) * np.sqrt(TRADING_DAYS)

        # Strategy: long the fwd_vol "asset" when slope is in bottom quintile
        # (cascade predicts vol will FALL... so we should SHORT vol instead)
        # Wait, the relationship is: high slope = low forward vol (negative Spearman)
        # So: high slope → short vol; low slope → long vol
        threshold = s.quantile(0.20)  # bottom quintile
        # When slope is below threshold (very negative), vol is bottoming → vol about to rise
        # So we should LONG vol
        signal = (s < threshold).astype(int)
        # Position in vol (fwd_vol): 1 if long, 0 if flat
        # Vol "return" is the change in fwd_vol (rough proxy)
        vol_change = fwd_vol.diff()
        # Strategy return: signal * vol_change
        # (this is a toy model; in reality we'd use a vol instrument)
        valid = signal.notna() & vol_change.notna()
        strat = signal[valid] * vol_change[valid]
        bh = vol_change[valid]
        if strat.std() > 0:
            sharpe_strat = strat.mean() / strat.std() * np.sqrt(TRADING_DAYS)
            sharpe_bh = bh.mean() / bh.std() * np.sqrt(TRADING_DAYS)
            print(f"  {asset}: Sharpe (long vol when bottom-quintile slope) = {sharpe_strat:.3f}  vs  buy-and-hold vol = {sharpe_bh:.3f}")

    out_path = RESULTS_DIR / "vol_timing_strategy.json"
    with open(out_path, "w") as f:
        json.dump({"note": "vol-timing strategy based on cascade slope",
                   "pre-registered_params": {
                       "inner_window": INNER_WINDOW,
                       "zscore_lookback": ZSCORE_LOOKBACK,
                       "forward_days": FORWARD_DAYS,
                       "vol_target": VOL_TARGET,
                   }}, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
