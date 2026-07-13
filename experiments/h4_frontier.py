"""H4 frontier extension: does the vol-peak effect hold in frontier markets?

Replicates the vol-peak analysis on the frontier ETF sample:
- EZA (iShares MSCI South Africa) — SSA proxy
- EWZ (iShares MSCI Brazil) — LatAm
- INDA (iShares MSCI India) — South Asia
- vs SPY (developed, control)

The hypothesis (H4): the cascade's vol-peak effect differs systematically
between developed and frontier markets. We test:
1. Per-asset Spearman rho of slope -> forward vol
2. Effect size comparison: frontier vs developed
3. Whether frontier markets show STRONGER vol-peak signal (consistent
   with the Brunnermeier-Pedersen liquidity-spiral hypothesis:
   thin markets amplify vol-of-vol dynamics)
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
from volcascade.io import load_prices  # noqa: E402

RESULTS_DIR = ROOT / "results"

FRONTIER_TICKERS = ["EZA", "EWZ", "INDA", "SPY"]


def analyze(rets: pd.Series, asset: str, inner_window=10, zscore_lookback=120, forward_days=5):
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=inner_window)
    z = zscore(cascade, lookback=zscore_lookback)
    sample = z[1]
    if isinstance(sample, pd.DataFrame):
        z_s = {k: z[k][asset] for k in [1, 2, 3, 4]}
    else:
        z_s = dict(z)
    s = slope(z_s)

    fwd_vol = pd.Series(np.nan, index=rets.index)
    fwd_ret = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - forward_days):
        fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + forward_days].std())
        fwd_ret.iloc[i] = float(rets.iloc[i + forward_days] / rets.iloc[i] - 1.0)

    out = {"asset": asset, "n_days": int(len(rets))}
    for name, series in [("forward_vol", fwd_vol), ("forward_return", fwd_ret)]:
        valid = series.notna() & s.notna()
        n = int(valid.sum())
        if n < 100:
            continue
        r_p, p_p = sps.pearsonr(s[valid], series[valid])
        r_s, p_s = sps.spearmanr(s[valid], series[valid])
        out[f"{name}_pearson_r"] = float(r_p)
        out[f"{name}_pearson_p"] = float(p_p)
        out[f"{name}_spearman_r"] = float(r_s)
        out[f"{name}_spearman_p"] = float(p_s)
        out[f"{name}_n"] = n
    return out


def main() -> None:
    print("=" * 78)
    print("H4: frontier vs developed vol-peak effect")
    print("=" * 78)

    print(f"\nloading {FRONTIER_TICKERS} (2007-2024, longest available for frontier)...")
    t0 = time.time()
    prices = load_prices(FRONTIER_TICKERS, start="2007-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days x {returns.shape[1]} tickers in {time.time()-t0:.1f}s\n")

    results = []
    for asset in returns.columns:
        rets = returns[asset].dropna()
        out = analyze(rets, asset)
        results.append(out)
        r = out.get("forward_vol_spearman_r")
        p = out.get("forward_vol_spearman_p")
        print(f"  {asset}: n={out['n_days']}, slope->vol Spearman={r:+.4f}  p={p:.2e}")

    df = pd.DataFrame(results)
    df["market_class"] = df["asset"].apply(
        lambda a: "developed" if a == "SPY" else "frontier"
    )
    # Drop rows where the Spearman is missing
    df = df.dropna(subset=["forward_vol_spearman_r"])

    print("\n" + "=" * 78)
    print("META: developed vs frontier")
    print("=" * 78)
    dev = df[df["market_class"] == "developed"]
    fr = df[df["market_class"] == "frontier"]
    print(f"\ndeveloped (SPY): n={len(dev)} assets")
    for _, r in dev.iterrows():
        print(f"  {r['asset']}: forward_vol Spearman={r['forward_vol_spearman_r']:+.4f}  p={r['forward_vol_spearman_p']:.2e}")
    print(f"\nfrontier: n={len(fr)} assets")
    for _, r in fr.iterrows():
        print(f"  {r['asset']}: forward_vol Spearman={r['forward_vol_spearman_r']:+.4f}  p={r['forward_vol_spearman_p']:.2e}")

    # Compare effect sizes
    dev_abs = dev["forward_vol_spearman_r"].abs().mean()
    fr_abs = fr["forward_vol_spearman_r"].abs().mean()
    print(f"\n|developed| = {dev_abs:.4f},  |frontier| mean = {fr_abs:.4f},  ratio = {fr_abs / dev_abs:.2f}x")

    out_path = RESULTS_DIR / "h4_frontier.json"
    with open(out_path, "w") as f:
        json.dump({"per_asset": [dict(r) for r in results],
                   "meta": {
                       "developed_spearman": float(dev["forward_vol_spearman_r"].iloc[0]),
                       "frontier_mean_spearman": float(fr["forward_vol_spearman_r"].mean()),
                       "n_frontier_assets": int(len(fr)),
                       "n_developed_assets": int(len(dev)),
                   }}, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
