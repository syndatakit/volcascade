"""Pre-registered OOS for direction prediction.

The cascade - momentum AUC = 0.596 was found by trying 9 methods and
picking the best. This is data dredging. Validate it out-of-sample:

1. Split data: 2000-2014 (train) and 2015-2024 (test)
2. On TRAIN, fit the best signal (cascade - momentum)
3. On TEST, evaluate AUC
4. Also try multiple OOS splits for robustness
5. Compare to in-sample performance
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps
from sklearn.metrics import roc_auc_score

ROOT = Path("/opt/data/volcascade")
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore
from volcascade.io import load_prices

INNER_WINDOW = 10
ZSCORE_LOOKBACK = 120


def main() -> None:
    print("=" * 78)
    print("PRE-REGISTERED OOS for cascade - momentum direction prediction")
    print("=" * 78)

    ASSETS = ["SPY", "XLE", "XLF", "XLV", "XLY"]
    print(f"\nloading {ASSETS} (2000-2024)...")
    prices = load_prices(ASSETS, start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days\n")

    OOS_SPLITS = [2014, 2016, 2018, 2020]
    rows = []
    for split_year in OOS_SPLITS:
        print(f"\n  Split year = {split_year}:")
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

            # Forward 1-day return
            fwd_1d = pd.Series(np.nan, index=rets.index)
            for i in range(len(rets) - 1):
                fwd_1d.iloc[i] = float(rets.iloc[i + 1] - rets.iloc[i])
            # 5-day momentum
            mom = rets.rolling(5, min_periods=3).sum()

            # Combined signal: cascade - momentum (pre-registered)
            valid = s.notna() & fwd_1d.notna() & mom.notna()
            if valid.sum() < 100:
                continue
            f = fwd_1d[valid]
            sv = s[valid]
            mv = mom[valid]
            sv_z = (sv - sv.mean()) / sv.std()
            mv_z = (mv - mv.mean()) / mv.std()
            signal = sv_z - mv_z
            is_pos = (f > 0).astype(int)

            # In-sample (full)
            try:
                auc_full = roc_auc_score(is_pos, signal)
            except Exception:
                continue
            # Out-of-sample
            train_mask = rets.index[valid] < f"{split_year}-01-01"
            test_mask = rets.index[valid] >= f"{split_year}-01-01"
            if train_mask.sum() < 50 or test_mask.sum() < 50:
                continue
            try:
                auc_train = roc_auc_score(is_pos[train_mask], signal[train_mask])
                auc_test = roc_auc_score(is_pos[test_mask], signal[test_mask])
            except Exception:
                continue
            # Ratio (test / full)
            ratio = auc_test / auc_full if abs(auc_full) > 0.01 else None
            rows.append({
                "asset": asset, "split_year": split_year,
                "auc_full": float(auc_full),
                "auc_train": float(auc_train),
                "auc_test": float(auc_test),
                "ratio": float(ratio) if ratio is not None else None,
            })
            sig = "*" if auc_test > 0.5 else " "
            print(f"    {sig} {asset}: full={auc_full:.3f}  train={auc_train:.3f}  test={auc_test:.3f}  ratio={ratio:+.3f}" if ratio is not None else f"    {sig} {asset}: ratio=n/a")

    # Aggregate
    df = pd.DataFrame(rows)
    print("\n" + "=" * 78)
    print("AGGREGATE OOS")
    print("=" * 78)
    if len(df) > 0:
        # Per-asset
        print(f"\n  Per-asset (median across splits):")
        for asset in ASSETS:
            sub = df[df["asset"] == asset]
            if len(sub) == 0:
                continue
            med_test = sub["auc_test"].median()
            n_above = (sub["auc_test"] > 0.5).sum()
            print(f"    {asset}: median test AUC = {med_test:.3f}  ({n_above}/{len(sub)} above 0.5)")
        # Aggregate
        print(f"\n  Aggregate (across all {len(df)} (asset, split) pairs):")
        print(f"    median test AUC: {df['auc_test'].median():.3f}")
        print(f"    fraction above 0.5: {(df['auc_test'] > 0.5).mean():.1%}")
        print(f"    median test/full ratio: {df['ratio'].median():.3f}")
        if df['auc_test'].median() > 0.5:
            print(f"    --> OOS AUC is {df['auc_test'].median():.3f}, ABOVE 0.5")
            print(f"    --> Generalizes (signal holds out-of-sample)")
        else:
            print(f"    --> OOS AUC is {df['auc_test'].median():.3f}, BELOW 0.5")
            print(f"    --> Does NOT generalize (data dredging concern confirmed)")

    out_path = ROOT / "results" / "direction_oos.json"
    with open(out_path, "w") as f:
        json.dump({"per_pair": rows,
                   "summary": {
                       "n_pairs": int(len(df)),
                       "median_test_auc": float(df['auc_test'].median()) if len(df) > 0 else None,
                       "frac_above_05": float((df['auc_test'] > 0.5).mean()) if len(df) > 0 else None,
                       "median_test_full_ratio": float(df['ratio'].median()) if len(df) > 0 else None,
                   }}, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
