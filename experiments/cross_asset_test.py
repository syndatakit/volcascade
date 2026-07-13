"""Cross-asset extension: vol-peak effect on bonds, gold, oil, intl equity.

If the vol-peak is a GENERAL vol phenomenon (not specific to US equities),
it should hold on:
- TLT (20+ year Treasury bonds) — bond vol regime
- GLD (gold) — commodity vol regime
- USO (US oil fund) — commodity vol regime
- EFA (EAFE developed international equity) — international vol regime
- EEM (emerging market equity) — emerging vol regime

Tests Spearman(slope, forward vol) on each.
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

CROSS_ASSET_TICKERS = {
    "TLT": "20+ year Treasury bonds (long bond)",
    "GLD": "Gold (commodity)",
    "USO": "US Oil Fund (commodity/energy)",
    "EFA": "EAFE developed international equity",
    "EEM": "Emerging markets equity",
    "SPY": "S&P 500 (control)",
}


def analyze(rets: pd.Series, name: str, inner_window=10, zscore_lookback=120,
            forward_days=5) -> dict:
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=inner_window)
    z = zscore(cascade, lookback=zscore_lookback)
    sample = z[1]
    if isinstance(sample, pd.DataFrame):
        z_s = {k: z[k][name] for k in [1, 2, 3, 4]}
    else:
        z_s = dict(z)
    s = slope(z_s)
    fwd_vol = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - forward_days):
        fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + forward_days].std())
    valid = s.notna() & fwd_vol.notna()
    if valid.sum() < 50:
        return None
    r, p = sps.spearmanr(s[valid], fwd_vol[valid])
    return {"r": float(r), "p": float(p), "n": int(valid.sum())}


def main() -> None:
    print("=" * 78)
    print("CROSS-ASSET EXTENSION: vol-peak on bonds, gold, oil, intl equity")
    print("=" * 78)

    tickers = list(CROSS_ASSET_TICKERS.keys())
    print(f"\nloading {tickers} (2007-2024)...")
    t0 = time.time()
    prices = load_prices(tickers, start="2007-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    results = []
    print("=" * 78)
    print("RESULTS: Spearman(slope, forward 5-day vol) by asset class")
    print("=" * 78)
    for asset in returns.columns:
        rets = returns[asset].dropna()
        out = analyze(rets, asset)
        if out is None:
            print(f"  {asset}: insufficient data")
            continue
        results.append({
            "asset": asset,
            "asset_class": CROSS_ASSET_TICKERS[asset],
            **out,
        })
        sig = "*" if out["p"] < 0.05 else " "
        print(f"  {sig} {asset:6s} ({CROSS_ASSET_TICKERS[asset][:40]:40s}): "
              f"rho={out['r']:+.4f}  p={out['p']:.2e}  n={out['n']}")

    # Aggregate
    df = pd.DataFrame(results)
    n_sig = (df["r"] < 0).sum()  # all should be negative
    n_p = (df["p"] < 0.05).sum()
    print("\n" + "=" * 78)
    print("AGGREGATE")
    print("=" * 78)
    print(f"\n  total assets: {len(df)}")
    print(f"  negative direction: {n_sig}/{len(df)} ({n_sig / len(df):.0%})")
    print(f"  significant (p<0.05): {n_p}/{len(df)} ({n_p / len(df):.0%})")
    print(f"  median Spearman: {df['r'].median():+.4f}")

    out_path = RESULTS_DIR / "cross_asset_test.json"
    with open(out_path, "w") as f:
        json.dump({
            "per_asset": results,
            "summary": {
                "n_assets": int(len(df)),
                "n_negative": int(n_sig),
                "n_significant": int(n_p),
                "median_spearman": float(df["r"].median()),
            },
        }, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
