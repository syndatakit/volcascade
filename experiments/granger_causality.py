"""Granger causality: does the cascade slope LEAD or LAG vol regime changes?

If the cascade slope genuinely predicts future vol (causal relationship),
the lag of slope should Granger-cause forward vol. If slope is just
smoothing vol contemporaneously, Granger causality will be null.

Test: for each lag k = 1, 2, ..., 10, test whether slope_{t-k} Granger-
causes forward_vol_t (using the standard F-test from statsmodels).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps
from statsmodels.tsa.stattools import grangercausalitytests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore  # noqa: E402
from volcascade.io import SP500_SECTOR_ETFS, load_prices  # noqa: E402

RESULTS_DIR = ROOT / "results"

ASSETS = ["SPY", "XLE", "XLF", "XLV", "XLY"]


def main() -> None:
    print("=" * 78)
    print("GRANGER CAUSALITY: does cascade slope LEAD forward vol?")
    print("=" * 78)

    print(f"\nloading {ASSETS} (2000-2024)...")
    t0 = time.time()
    prices = load_prices(ASSETS, start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    print("=" * 78)
    print(f"GRANGER F-TEST: slope_lag(k) -> forward_vol_t  (k = 1..10)")
    print("=" * 78)

    rows = []
    for asset in ASSETS:
        rets = returns[asset].dropna()
        cascade = build(rets, orders=(1, 2, 3, 4), inner_window=10)
        z = zscore(cascade, lookback=120)
        sample = z[1]
        if isinstance(sample, pd.DataFrame):
            z_s = {k: z[k][asset] for k in [1, 2, 3, 4]}
        else:
            z_s = dict(z)
        s = slope(z_s)
        fwd_vol = pd.Series(np.nan, index=rets.index)
        for i in range(len(rets) - 5):
            fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + 5].std())

        # Build a DataFrame with slope (lag 0..5) and forward_vol
        df = pd.DataFrame({"fwd_vol": fwd_vol})
        for lag in [1, 2, 3, 5, 10]:
            df[f"slope_lag{lag}"] = s.shift(lag)
        df = df.dropna()

        # Granger test: slope_lag -> fwd_vol
        # statsmodels expects a 2D array with [effect, cause] columns
        print(f"\n  {asset}:")
        for lag in [1, 2, 3, 5, 10]:
            data = df[["fwd_vol", f"slope_lag{lag}"]].dropna().values
            try:
                # Test if slope_lag Granger-causes fwd_vol
                res = grangercausalitytests(data, maxlag=lag, verbose=False)
                f_stat = res[lag][0]["ssr_ftest"][0]
                p_val = res[lag][0]["ssr_ftest"][1]
                rows.append({
                    "asset": asset, "lag": lag,
                    "f_stat": float(f_stat), "p_value": float(p_val),
                })
                sig = "*" if p_val < 0.05 else " "
                print(f"    lag {lag:2d}: F={f_stat:.2f}  p={p_val:.2e}  {sig}")
            except Exception as e:
                print(f"    lag {lag:2d}: failed ({e})")

    # Summary
    df_res = pd.DataFrame(rows)
    if len(df_res) > 0:
        print("\n" + "=" * 78)
        print("AGGREGATE: fraction of (asset, lag) pairs with significant Granger causality")
        print("=" * 78)
        for lag in [1, 2, 3, 5, 10]:
            sub = df_res[df_res["lag"] == lag]
            n_sig = (sub["p_value"] < 0.05).sum()
            print(f"  lag {lag:2d}: {n_sig}/{len(sub)} assets significant (p<0.05)")
        # All assets, all lags
        n_total_sig = (df_res["p_value"] < 0.05).sum()
        n_total = len(df_res)
        print(f"\n  overall: {n_total_sig}/{n_total} ({n_total_sig/n_total:.0%}) significant")

    out_path = RESULTS_DIR / "granger_causality.json"
    with open(out_path, "w") as f:
        json.dump({
            "results": rows,
            "summary": {
                "n_total_pairs": int(len(df_res)),
                "n_significant": int((df_res["p_value"] < 0.05).sum()) if len(df_res) > 0 else 0,
                "frac_significant": float((df_res["p_value"] < 0.05).mean()) if len(df_res) > 0 else None,
            },
        }, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
