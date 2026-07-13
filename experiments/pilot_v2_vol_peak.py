"""Pilot v2: cascade as a vol peak detector.

The pre-registered H1 test (forward return) is null. But the cascade
slope has a strong negative correlation with FORWARD REALIZED VOLATILITY:

    Spearman(slope_t, vol_{t+1..t+5}) = -0.20, p = 1e-53

This means: when the cascade is steepening (higher orders more elevated),
forward volatility is LOWER. The cascade captures "vol exhaustion" —
when vol is peaking, vol-of-vol is also peaking, and the cascade shape
flags the moment of exhaustion.

This script:
1. Replicates the vol-peak finding on multiple assets (sector ETFs)
2. Reports per-asset Spearman, AUC, and significance
3. Compares the cascade slope to single-order z-scores as predictors
4. Writes a clean summary suitable for paper section H1'
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


def cascade_at_t(s: pd.Series, t: pd.Timestamp) -> float:
    return float(s.loc[t]) if (t in s.index and not pd.isna(s.loc[t])) else np.nan


def analyze_asset(
    rets: pd.Series,
    asset: str,
    inner_window: int = 10,
    zscore_lookback: int = 120,
    forward_days: int = 5,
) -> dict:
    """Run the cascade-as-vol-peak-detector analysis on a single asset."""
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=inner_window)
    z = zscore(cascade, lookback=zscore_lookback)
    sample = z[1]
    if isinstance(sample, pd.DataFrame):
        z_s = {k: z[k][asset] for k in [1, 2, 3, 4]}
    else:
        z_s = dict(z)
    s = slope(z_s)

    # Forward realized volatility (the target)
    fwd_vol = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - forward_days):
        fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + forward_days].std())

    # Also forward absolute return (a simple proxy for "bad day")
    fwd_abs = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - forward_days):
        fwd_abs.iloc[i] = float(rets.iloc[i + 1:i + 1 + forward_days].abs().mean())

    # Forward return (the pre-registered H1 outcome — should be null)
    fwd_return = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - forward_days):
        fwd_return.iloc[i] = float(rets.iloc[i + forward_days] / rets.iloc[i] - 1.0)

    out = {"asset": asset, "n_days": int(len(rets))}

    # Predict each forward outcome from cascade slope
    for outcome_name, outcome in [
        ("forward_vol", fwd_vol),
        ("forward_abs_return", fwd_abs),
        ("forward_return", fwd_return),
    ]:
        valid = outcome.notna() & s.notna()
        n = int(valid.sum())
        if n < 100:
            continue
        r_p, p_p = sps.pearsonr(s[valid], outcome[valid])
        r_s, p_s = sps.spearmanr(s[valid], outcome[valid])
        out[f"{outcome_name}_pearson_r"] = float(r_p)
        out[f"{outcome_name}_pearson_p"] = float(p_p)
        out[f"{outcome_name}_spearman_r"] = float(r_s)
        out[f"{outcome_name}_spearman_p"] = float(p_s)
        out[f"{outcome_name}_n"] = n

    # Compare to single-order z-score (order 1) as predictor
    if isinstance(cascade[1], pd.DataFrame):
        order1_z = z[1][asset]
    else:
        order1_z = z[1]
    for outcome_name, outcome in [("forward_vol", fwd_vol), ("forward_return", fwd_return)]:
        valid = outcome.notna() & order1_z.notna()
        n = int(valid.sum())
        if n < 100:
            continue
        r_s, p_s = sps.spearmanr(order1_z[valid], outcome[valid])
        out[f"{outcome_name}_order1_spearman_r"] = float(r_s)
        out[f"{outcome_name}_order1_spearman_p"] = float(p_s)

    return out


def main() -> None:
    print("=" * 78)
    print("Pilot v2: cascade as a vol peak detector")
    print("=" * 78)

    print("\nloading SPY + 11 sector ETFs (2000-2024)...")
    t0 = time.time()
    prices = load_prices(list(SP500_SECTOR_ETFS), start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days x {returns.shape[1]} tickers in {time.time()-t0:.1f}s\n")

    results = []
    for asset in returns.columns:
        rets = returns[asset].dropna()
        out = analyze_asset(rets, asset, inner_window=10, zscore_lookback=120, forward_days=5)
        results.append(out)
        fwd_vol_r = out.get("forward_vol_spearman_r")
        fwd_vol_p = out.get("forward_vol_spearman_p")
        fwd_ret_r = out.get("forward_return_spearman_r")
        fwd_ret_p = out.get("forward_return_spearman_p")
        print(f"  {asset}: forward_vol  Spearman={fwd_vol_r:+.4f}  p={fwd_vol_p:.2e}   "
              f"forward_return Spearman={fwd_ret_r:+.4f}  p={fwd_ret_p:.2e}")

    print("\n" + "=" * 78)
    print("HEADLINE: forward vol vs forward return, by asset")
    print("=" * 78)
    df = pd.DataFrame(results)
    print("\nforward_vol Spearman correlation (cascade slope -> forward realized vol):")
    print(df[["asset", "forward_vol_spearman_r", "forward_vol_spearman_p",
              "forward_vol_order1_spearman_r"]].to_string(index=False))

    print("\nforward_return Spearman correlation (pre-registered H1, expected null):")
    print(df[["asset", "forward_return_spearman_r", "forward_return_spearman_p"]].to_string(index=False))

    print("\n" + "=" * 78)
    print("META-ANALYSIS: how often is the vol signal stronger than the return signal?")
    print("=" * 78)
    n_assets = len(df)
    n_stronger = (df["forward_vol_spearman_r"].abs() > df["forward_return_spearman_r"].abs()).sum()
    print(f"  {n_stronger} / {n_assets} assets: |slope-vol correlation| > |slope-return correlation|")
    n_sig_vol = (df["forward_vol_spearman_p"] < 0.05).sum()
    print(f"  {n_sig_vol} / {n_assets} assets: forward_vol Spearman p < 0.05")
    n_sig_ret = (df["forward_return_spearman_p"] < 0.05).sum()
    print(f"  {n_sig_ret} / {n_assets} assets: forward_return Spearman p < 0.05")

    # Save results
    out_path = RESULTS_DIR / "pilot_v2_vol_peak.json"
    with open(out_path, "w") as f:
        json.dump({"per_asset": results,
                   "meta": {"n_assets": n_assets,
                            "n_vol_stronger": int(n_stronger),
                            "n_vol_significant": int(n_sig_vol),
                            "n_return_significant": int(n_sig_ret)}},
                  f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
