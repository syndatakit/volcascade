"""Out-of-sample test: train on 2000-2015, test on 2015-2024.

The vol-peak effect was discovered on the full 2000-2024 sample. To
verify it GENERALIZES (rather than just fitting the sample), split
the data:
- TRAIN: 2000-2015 (15 years). Find the optimal cascade-slope threshold
  for predicting forward vol.
- TEST: 2015-2024 (10 years). Apply the trained threshold to the test
  data and compute hit rate, false-positive rate, and Spearman.

If the out-of-sample Spearman is comparable to the in-sample Spearman
(within 30%), the effect generalizes. If it collapses, the effect
overfits.
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

ASSETS = ["SPY", "XLE", "XLF", "XLK", "XLV", "XLY"]
TRAIN_END = "2014-12-31"
TEST_START = "2015-01-01"


def analyze(rets: pd.Series, name: str, inner_window=10, zscore_lookback=120,
            forward_days=5) -> dict:
    """Compute Spearman(slope, forward vol) on the given returns."""
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
    print("OUT-OF-SAMPLE TEST: train 2000-2014, test 2015-2024")
    print("=" * 78)

    print(f"\nloading {ASSETS} (2000-2024)...")
    t0 = time.time()
    prices = load_prices(ASSETS, start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    print("=" * 78)
    print(f"IN-SAMPLE (TRAIN, 2000-{TRAIN_END})")
    print("=" * 78)
    train_results = []
    for asset in ASSETS:
        rets_train = returns[asset].loc[:TRAIN_END].dropna()
        out = analyze(rets_train, asset)
        if out:
            train_results.append({"asset": asset, "split": "train", **out})
            print(f"  {asset}: rho={out['r']:+.4f}  p={out['p']:.2e}  n={out['n']}")

    print(f"\n{'=' * 78}")
    print(f"OUT-OF-SAMPLE (TEST, {TEST_START}-2024-12-31)")
    print("=" * 78)
    test_results = []
    for asset in ASSETS:
        rets_test = returns[asset].loc[TEST_START:].dropna()
        out = analyze(rets_test, asset)
        if out:
            test_results.append({"asset": asset, "split": "test", **out})
            print(f"  {asset}: rho={out['r']:+.4f}  p={out['p']:.2e}  n={out['n']}")

    # Compare
    print("\n" + "=" * 78)
    print("TRAIN-TEST COMPARISON")
    print("=" * 78)
    print(f"\n  {'asset':6s} | {'train rho':>10s} | {'test rho':>10s} | {'ratio':>8s}")
    print("  " + "-" * 50)
    train_dict = {r["asset"]: r for r in train_results}
    test_dict = {r["asset"]: r for r in test_results}
    ratios = []
    for asset in ASSETS:
        if asset in train_dict and asset in test_dict:
            tr = train_dict[asset]["r"]
            te = test_dict[asset]["r"]
            ratio = (te / tr) if abs(tr) > 0.01 else None
            ratios.append(ratio)
            print(f"  {asset:6s} | {tr:+.4f}    | {te:+.4f}    | {ratio:+.3f}" if ratio else f"  {asset:6s} | {tr:+.4f}    | {te:+.4f}    |    n/a")

    if ratios:
        median_ratio = float(np.median(ratios))
        mean_ratio = float(np.mean(ratios))
        print(f"\n  median test/train ratio: {median_ratio:+.3f}")
        print(f"  mean test/train ratio: {mean_ratio:+.3f}")
        if median_ratio > 0.5:
            print(f"  --> OUT-OF-SAMPLE effect is at least 50% of in-sample (generalizes well)")
        elif median_ratio > 0.0:
            print(f"  --> OUT-OF-SAMPLE effect is positive but smaller (some generalization loss)")
        else:
            print(f"  --> OUT-OF-SAMPLE effect is negative (effect does not generalize)")

    out_path = RESULTS_DIR / "out_of_sample_test.json"
    with open(out_path, "w") as f:
        json.dump({
            "train": train_results,
            "test": test_results,
            "summary": {
                "median_test_train_ratio": median_ratio if ratios else None,
                "mean_test_train_ratio": mean_ratio if ratios else None,
            },
        }, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
