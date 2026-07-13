"""H1 sensitivity v2: predict forward VOLATILITY and vol-of-vol (not return).

The cascade is a vol-of-vol statistic. Its natural target is forward
vol-of-vol, not forward return. Testing return as the outcome may be
the wrong framing. This script:

1. Extends time window to 2000-2024 (25 years) for more regime variation
2. Tests three outcomes: forward return, forward realized vol, forward vol-of-vol
3. For each, runs the spike-tertile test and the continuous correlation test
4. Also tests the cascade AVERAGED OVER A WINDOW (past K days' mean slope)

If the cascade is informative about anything, it should be most
informative about forward vol-of-vol.
"""

from __future__ import annotations

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


def main() -> None:
    print("=" * 78)
    print("H1 sensitivity v2 — predicting forward vol, vol-of-vol, return")
    print("=" * 78)

    print("\nloading SPY (2000-01-01 to 2024-12-31)...")
    t0 = time.time()
    prices = load_prices(["SPY"], start="2000-01-01", end="2024-12-31")
    rets = np.log(prices / prices.shift(1)).dropna()["SPY"]
    print(f"  loaded {len(rets)} days in {time.time()-t0:.1f}s\n")

    # Build cascade (use moderate parameters from v1 sweep)
    iw = 10
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=iw)
    z = zscore(cascade, lookback=120)
    sample = z[1]
    if isinstance(sample, pd.DataFrame):
        z_spy = {k: z[k]["SPY"] for k in [1, 2, 3, 4]}
    else:
        z_spy = dict(z)
    s = slope(z_spy).dropna()

    # Forward outcomes
    forward_days = 5
    fwd_return = pd.Series(np.nan, index=rets.index)
    fwd_vol = pd.Series(np.nan, index=rets.index)
    fwd_vol_of_vol = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - forward_days):
        fwd_return.iloc[i] = float(rets.iloc[i + forward_days] / rets.iloc[i] - 1.0)
        fwd_vol.iloc[i] = float(rets.iloc[i:i + forward_days].std())
        # Realized vol of realized vol: vol of order-1 in the forward window
        if i + forward_days < len(cascade[1]) - 20:
            order1_window = cascade[1].iloc[i + 5:i + forward_days + 5]  # skip the first 5 days which are the spike
            if len(order1_window.dropna()) > 5:
                fwd_vol_of_vol.iloc[i] = float(order1_window.std())

    # Also test "rolling window" cascade slope (mean over past K days)
    s_windowed_20 = s.rolling(20, min_periods=5).mean()

    print(f"valid spike counts:")
    valid = fwd_return.notna() & s.notna()
    print(f"  forward_return: {valid.sum()}")
    valid_vol = fwd_vol.notna() & s.notna()
    print(f"  forward_vol: {valid_vol.sum()}")
    valid_vov = fwd_vol_of_vol.notna() & s.notna()
    print(f"  forward_vol_of_vol: {valid_vov.sum()}")

    print("\n" + "=" * 78)
    print("RESULTS: predicting each forward outcome from cascade slope")
    print("=" * 78)

    for outcome_name, outcome in [
        ("forward_return", fwd_return),
        ("forward_vol", fwd_vol),
        ("forward_vol_of_vol", fwd_vol_of_vol),
    ]:
        print(f"\n--- outcome: {outcome_name} ---")
        for metric_name, mseries in [("slope_today", s), ("slope_avg20", s_windowed_20)]:
            valid = outcome.notna() & mseries.notna()
            n = int(valid.sum())
            if n < 100:
                print(f"  {metric_name}: n={n} (insufficient)")
                continue

            # Pearson and Spearman
            r_p, p_p = sps.pearsonr(mseries[valid], outcome[valid])
            r_s, p_s = sps.spearmanr(mseries[valid], outcome[valid])

            # AUC for predicting extreme outcomes (top/bottom quartile)
            high = outcome[valid] >= outcome[valid].quantile(0.75)
            low = outcome[valid] <= outcome[valid].quantile(0.25)
            m_high = mseries[valid][high]
            m_low = mseries[valid][low]
            m_mid = mseries[valid][~high & ~low]
            if len(m_high) > 5 and len(m_low) > 5:
                u_h, _ = sps.mannwhitneyu(m_high, m_mid, alternative="two-sided")
                auc_high = u_h / (len(m_high) * len(m_mid))
                u_l, _ = sps.mannwhitneyu(m_low, m_mid, alternative="two-sided")
                auc_low = u_l / (len(m_low) * len(m_mid))
            else:
                auc_high, auc_low = None, None

            # Spike-tertile: |z^(1)| > 1.5, forward outcome by slope tertile
            z1 = rets / rets.rolling(60).std()
            spikes = z1.abs() > 1.5
            spike_dates = z1.index[spikes]
            recs = []
            for d in spike_dates:
                if d not in mseries.index or d not in outcome.index:
                    continue
                m_val = mseries.loc[d]
                o_val = outcome.loc[d]
                if pd.isna(m_val) or pd.isna(o_val):
                    continue
                recs.append({"m": float(m_val), "o": float(o_val)})
            if len(recs) >= 30:
                df_sp = pd.DataFrame(recs)
                df_sp["tertile"] = pd.qcut(df_sp["m"], 3, labels=["flat", "moderate", "steep"])
                flat_o = df_sp.loc[df_sp["tertile"] == "flat", "o"].values
                steep_o = df_sp.loc[df_sp["tertile"] == "steep", "o"].values
                u_sp, p_sp = sps.mannwhitneyu(flat_o, steep_o, alternative="two-sided")
                ratio = abs(np.median(steep_o) / np.median(flat_o)) if np.median(flat_o) != 0 else np.nan
            else:
                u_sp, p_sp, ratio = None, None, None

            print(f"\n  {metric_name} (n={n}):")
            print(f"    Pearson r = {r_p:+.4f}  (p={p_p:.2e})")
            print(f"    Spearman r = {r_s:+.4f}  (p={p_s:.2e})")
            if auc_high is not None:
                print(f"    AUC(high vs mid) = {auc_high:.4f}")
                print(f"    AUC(low vs mid) = {auc_low:.4f}")
            if ratio is not None:
                print(f"    spike-tertile: n_spikes={len(recs)}, ratio={ratio:.3f}, p={p_sp:.2e}")


if __name__ == "__main__":
    main()
