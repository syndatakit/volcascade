"""Vol-peak sensitivity sweep across the full parameter grid.

Vary all the parameters at once and report:
- Fraction of parameter combinations with significant Spearman
- Median Spearman across combinations
- Best (highest |Spearman|) parameter combination
- Whether the effect is robust to specification choices

Parameters swept:
  - inner_window: [5, 10, 20, 40]
  - zscore_lookback: [60, 120, 252]
  - forward_days: [1, 2, 3, 5, 10, 20]
  - n_orders: [3, 4]  # cascade order cutoffs

Total combinations: 4 * 3 * 6 * 2 = 144 per asset
Assets: SPY, XLK, XLE, XLF, XLV, XLY (6 sector ETFs)

Output: a table showing, for each asset, the fraction of combinations
with p < 0.05 and the median Spearman. A "clean" result would show
> 80% of combinations significant and consistent direction.
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

ASSETS = ["SPY", "XLK", "XLE", "XLF", "XLV", "XLY"]
INNER_WINDOWS = [5, 10, 20, 40]
ZSCORE_LOOKBACKS = [60, 120, 252]
FORWARD_DAYS_LIST = [1, 2, 3, 5, 10, 20]
N_ORDERS_LIST = [3, 4]


def analyze(rets, asset_name, inner_window, zscore_lookback, forward_days, n_orders):
    """Single analysis: cascade -> slope -> forward vol Spearman."""
    orders = tuple(range(1, n_orders + 1))
    cascade = build(rets, orders=orders, inner_window=inner_window)
    z = zscore(cascade, lookback=zscore_lookback)
    sample = z[1]
    if isinstance(sample, pd.DataFrame):
        z_s = {k: z[k][asset_name] for k in orders}
    else:
        z_s = dict(z)
    s = slope(z_s)

    fwd_vol = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - forward_days):
        fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + forward_days].std())

    valid = s.notna() & fwd_vol.notna()
    n = int(valid.sum())
    if n < 100:
        return None
    r, p = sps.spearmanr(s[valid], fwd_vol[valid])
    return {"spearman_r": float(r), "spearman_p": float(p), "n": n}


def main() -> None:
    print("=" * 78)
    print("VOL-PEAK SENSITIVITY: 144 parameter combinations x 6 assets")
    print("=" * 78)

    print(f"\nloading {ASSETS} (2000-2024)...")
    t0 = time.time()
    prices = load_prices(ASSETS, start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    all_rows = []
    n_total = len(INNER_WINDOWS) * len(ZSCORE_LOOKBACKS) * len(FORWARD_DAYS_LIST) * len(N_ORDERS_LIST)
    t0 = time.time()
    done = 0
    for asset in ASSETS:
        rets = returns[asset].dropna()
        for iw in INNER_WINDOWS:
            for zl in ZSCORE_LOOKBACKS:
                for fd in FORWARD_DAYS_LIST:
                    for no in N_ORDERS_LIST:
                        res = analyze(rets, asset, iw, zl, fd, no)
                        if res is not None:
                            all_rows.append({
                                "asset": asset, "inner_window": iw,
                                "zscore_lookback": zl, "forward_days": fd,
                                "n_orders": no, **res})
                        done += 1
        print(f"  {asset}: done ({time.time()-t0:.1f}s)")

    df = pd.DataFrame(all_rows)
    print(f"\n{len(df)} valid parameter combinations\n")

    print("=" * 78)
    print("PER-ASSET SUMMARY")
    print("=" * 78)
    for asset in ASSETS:
        sub = df[df["asset"] == asset]
        n_total = len(sub)
        n_sig = (sub["spearman_p"] < 0.05).sum()
        n_neg = (sub["spearman_r"] < 0).sum()
        med_r = sub["spearman_r"].median()
        iqr_r = sub["spearman_r"].quantile(0.75) - sub["spearman_r"].quantile(0.25)
        print(f"\n  {asset}:")
        print(f"    n combinations: {n_total}")
        print(f"    significant (p<0.05): {n_sig}/{n_total} ({n_sig/n_total:.0%})")
        print(f"    negative direction: {n_neg}/{n_total} ({n_neg/n_total:.0%})")
        print(f"    Spearman median: {med_r:+.4f}  IQR: {iqr_r:.4f}")
        # Best combination
        best = sub.loc[sub["spearman_p"].idxmin()]
        print(f"    best: iw={int(best['inner_window'])}, zl={int(best['zscore_lookback'])}, "
              f"fd={int(best['forward_days'])}, no={int(best['n_orders'])}: "
              f"r={best['spearman_r']:+.4f}, p={best['spearman_p']:.2e}")

    # Aggregate summary
    n_total = len(df)
    n_sig = (df["spearman_p"] < 0.05).sum()
    n_neg = (df["spearman_r"] < 0).sum()
    print("\n" + "=" * 78)
    print("AGGREGATE SUMMARY (all assets, all combinations)")
    print("=" * 78)
    print(f"  total combinations: {n_total}")
    print(f"  significant (p<0.05): {n_sig}/{n_total} ({n_sig/n_total:.0%})")
    print(f"  negative direction: {n_neg}/{n_total} ({n_neg/n_total:.0%})")
    print(f"  median Spearman: {df['spearman_r'].median():+.4f}")

    out_csv = RESULTS_DIR / "vol_peak_sensitivity.csv"
    df.to_csv(out_csv, index=False)
    out_json = RESULTS_DIR / "vol_peak_sensitivity.json"
    with open(out_json, "w") as f:
        json.dump({
            "per_asset": {
                a: {
                    "n_combinations": int(len(df[df["asset"] == a])),
                    "n_significant": int((df[df["asset"] == a]["spearman_p"] < 0.05).sum()),
                    "n_negative": int((df[df["asset"] == a]["spearman_r"] < 0).sum()),
                    "median_spearman": float(df[df["asset"] == a]["spearman_r"].median()),
                } for a in ASSETS
            },
            "aggregate": {
                "n_total": int(n_total),
                "n_significant": int(n_sig),
                "n_negative": int(n_neg),
                "median_spearman": float(df["spearman_r"].median()),
            },
        }, f, indent=2)
    print(f"\nresults saved to {out_csv} and {out_json}")

    # Verdict
    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    if n_sig / n_total > 0.80:
        print("  ROBUST: > 80% of parameter combinations are significant")
    elif n_sig / n_total > 0.50:
        print("  MODERATELY ROBUST: > 50% of combinations significant")
    else:
        print("  WEAK: < 50% of combinations significant")
    if n_neg / n_total > 0.95:
        print("  CONSISTENT DIRECTION: > 95% of combinations negative")
    elif n_neg / n_total > 0.80:
        print("  MOSTLY CONSISTENT: > 80% negative")
    else:
        print(f"  MIXED: only {n_neg/n_total:.0%} negative")


if __name__ == "__main__":
    main()
