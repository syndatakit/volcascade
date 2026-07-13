"""H2 v2: use cascade's vol-peak signal (slope) for exit detection.

The original H2 used "cascade convergence = spread of z-scores falling
below 60-day median" as the exit signal. This was the WRONG METRIC
for the cascade. The cascade's actual signal is the SLOPE (vol-peak
detector). When the cascade slope is very negative, vol is peaking
and about to come down — that IS the exit.

Hypothesis: when the cascade slope (vol-peak signal) drops below its
60-day median, the regime ends SOONER than the naive order-1-MA
baseline. This is the cascade's natural exit signal, not the spread.

Test:
- Detect regime entries (forward vol > 1.5x trailing median).
- At each entry, check whether the cascade slope (NEGATIVE = vol-peak)
  fires before the naive order-1-MA exit.
- Compare lead time: cascade slope exit vs naive order-1-MA exit.
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


def main() -> None:
    print("=" * 78)
    print("H2 v2: cascade SLOPE (vol-peak) as exit signal vs naive order-1-MA")
    print("=" * 78)

    print("\nloading SPY + 5 sector ETFs (2000-2024)...")
    t0 = time.time()
    prices = load_prices(list(SP500_SECTOR_ETFS)[:6], start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    # Define regime: forward 5-day realized vol > 1.5x trailing median
    fwd_vol = returns.rolling(5, min_periods=1).std().shift(-5)
    fwd_vol_trail_med = fwd_vol.rolling(60, min_periods=30).median().shift(1)
    is_regime = fwd_vol > 1.5 * fwd_vol_trail_med

    results = []
    for asset in returns.columns:
        rets = returns[asset].dropna()
        cascade = build(rets, orders=(1, 2, 3, 4), inner_window=10)
        z = zscore(cascade, lookback=120)
        sample = z[1]
        if isinstance(sample, pd.DataFrame):
            z_s = {k: z[k][asset] for k in [1, 2, 3, 4]}
        else:
            z_s = dict(z)

        # Cascade SLOPE (vol-peak signal)
        s = slope(z_s)
        s_trail_med = s.rolling(60, min_periods=30).median()
        # Exit signal: slope is very negative (below 25th percentile of trailing)
        s_trail_p25 = s.rolling(60, min_periods=30).quantile(0.25)
        cascade_exit_v2 = s < s_trail_p25  # slope very low = vol peaking

        # Also: rolling 20-day mean slope (smoother signal)
        s_avg = s.rolling(20, min_periods=5).mean()
        s_avg_trail_p25 = s_avg.rolling(60, min_periods=30).quantile(0.25)
        cascade_exit_avg = s_avg < s_avg_trail_p25

        # Naive order-1-MA baseline
        order1 = z_s[1]
        o1_ma = order1.rolling(60, min_periods=30).mean()
        naive_exit = order1 < o1_ma

        # Find regime transitions
        regime = is_regime[asset]
        regime_change = regime.astype(int).diff().fillna(0)
        regime_starts = regime_change[regime_change == 1].index

        n_regimes = len(regime_starts)
        if n_regimes < 20:
            print(f"  {asset}: only {n_regimes} regimes, skipping")
            continue

        # For each regime entry, find:
        # - ground-truth exit (forward vol falling below threshold)
        # - cascade-exit-v2 (slope-based) first fire
        # - cascade-exit-avg (smoothed slope) first fire
        # - naive-exit first fire
        cascade_v2_leads = []
        cascade_avg_leads = []
        naive_leads = []
        for start in regime_starts:
            end_window = start + pd.Timedelta(days=60)
            # Ground truth exit: first day in window where regime becomes False
            regime_window = regime.loc[start:end_window]
            exits_gt = regime_window[~regime_window]
            if len(exits_gt) == 0:
                continue  # regime lasted > 60 days, skip
            gt_exit = exits_gt.index[0]

            # Cascade v2 exit (raw slope)
            exits = cascade_exit_v2.loc[start:end_window]
            exits = exits[exits]
            if len(exits) > 0:
                cascade_v2_leads.append((exits.index[0] - gt_exit).days)

            # Cascade avg exit (smoothed)
            exits = cascade_exit_avg.loc[start:end_window]
            exits = exits[exits]
            if len(exits) > 0:
                cascade_avg_leads.append((exits.index[0] - gt_exit).days)

            # Naive exit
            exits = naive_exit.loc[start:end_window]
            exits = exits[exits]
            if len(exits) > 0:
                naive_leads.append((exits.index[0] - gt_exit).days)

        # Lead time: NEGATIVE = exit fires BEFORE ground truth (good!)
        out = {
            "asset": asset,
            "n_regimes": n_regimes,
            "n_cascade_v2_signals": len(cascade_v2_leads),
            "n_cascade_avg_signals": len(cascade_avg_leads),
            "n_naive_signals": len(naive_leads),
            "cascade_v2_mean_lead": float(np.mean(cascade_v2_leads)) if cascade_v2_leads else None,
            "cascade_avg_mean_lead": float(np.mean(cascade_avg_leads)) if cascade_avg_leads else None,
            "naive_mean_lead": float(np.mean(naive_leads)) if naive_leads else None,
        }
        results.append(out)
        print(f"\n  {asset}: n_regimes={n_regimes}")
        print(f"    cascade_v2 (raw slope): mean lead = {out['cascade_v2_mean_lead']:.2f} days, "
              f"fired in {out['n_cascade_v2_signals']}/{n_regimes} regimes")
        print(f"    cascade_avg (smooth): mean lead = {out['cascade_avg_mean_lead']:.2f} days, "
              f"fired in {out['n_cascade_avg_signals']}/{n_regimes} regimes")
        print(f"    naive:                  mean lead = {out['naive_mean_lead']:.2f} days, "
              f"fired in {out['n_naive_signals']}/{n_regimes} regimes")

    df = pd.DataFrame(results)
    print("\n" + "=" * 78)
    print("AGGREGATE (mean lead = days BEFORE ground-truth exit; negative = earlier)")
    print("=" * 78)
    valid = df.dropna(subset=["cascade_v2_mean_lead", "cascade_avg_mean_lead", "naive_mean_lead"])
    if len(valid) > 0:
        print(f"\n  mean lead time (days before ground-truth exit):")
        print(f"    cascade_v2 (raw slope): {valid['cascade_v2_mean_lead'].mean():+.2f}")
        print(f"    cascade_avg (smoothed): {valid['cascade_avg_mean_lead'].mean():+.2f}")
        print(f"    naive:                  {valid['naive_mean_lead'].mean():+.2f}")

        # Paired t-test: cascade_v2 vs naive
        t, p = sps.ttest_rel(valid["cascade_v2_mean_lead"], valid["naive_mean_lead"])
        print(f"\n  paired t-test (cascade_v2 vs naive): t={t:+.3f}, p={p:.4f}")
        if valid["cascade_v2_mean_lead"].mean() < valid["naive_mean_lead"].mean():
            print(f"  --> cascade_v2 fires EARLIER than naive (more negative lead)")

        t, p = sps.ttest_rel(valid["cascade_avg_mean_lead"], valid["naive_mean_lead"])
        print(f"  paired t-test (cascade_avg vs naive): t={t:+.3f}, p={p:.4f}")

    out_path = RESULTS_DIR / "h2_v2_vol_peak_exit.json"
    with open(out_path, "w") as f:
        json.dump({"per_asset": [dict(r) for r in results],
                   "summary": {
                       "n_assets": int(len(df)),
                       "cascade_v2_mean_lead": float(valid["cascade_v2_mean_lead"].mean()) if len(valid) > 0 else None,
                       "cascade_avg_mean_lead": float(valid["cascade_avg_mean_lead"].mean()) if len(valid) > 0 else None,
                       "naive_mean_lead": float(valid["naive_mean_lead"].mean()) if len(valid) > 0 else None,
                   }}, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
