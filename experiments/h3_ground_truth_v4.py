"""H3 ground-truth v4: Wasserstein distance + cross-correlation profile.

In v3, the F-magnitude gave AUC 0.60, p=0.088. Try two new framings:

1. Wasserstein distance: measure the distributional difference between
   AAPL and XLK returns in a window around each event. Higher Wasserstein
   = more divergent distributions = more idiosyncratic.

2. Cross-correlation profile: at each cascade order, compute the
   correlation of (AAPL, XLK) z-scores in the event window. The PROFILE
   of correlations across orders should differ:
   - Idiosyncratic: low correlation at order 1, recovers at higher orders
   - Systemic: high correlation at all orders
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps
from scipy.stats import wasserstein_distance
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from volcascade import build, zscore  # noqa: E402
from volcascade.io import load_prices  # noqa: E402
from h3_ground_truth import aapl_earnings_dates, fomc_dates  # noqa: E402

RESULTS_DIR = ROOT / "results"


def main() -> None:
    print("=" * 78)
    print("H3 v4: Wasserstein distance + cross-correlation profile")
    print("=" * 78)

    events = aapl_earnings_dates() + fomc_dates()
    print(f"\n{len(events)} curated events")

    print("\nloading AAPL, XLK (2015-2024)...")
    t0 = time.time()
    prices = load_prices(["AAPL", "XLK"], start="2015-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    aapl_cascade = build(returns["AAPL"], orders=(1, 2, 3, 4), inner_window=10)
    aapl_z = zscore(aapl_cascade, lookback=120)
    xlk_cascade = build(returns["XLK"], orders=(1, 2, 3, 4), inner_window=10)
    xlk_z = zscore(xlk_cascade, lookback=120)

    records = []
    t0 = time.time()
    for i, ev in enumerate(events):
        if (i + 1) % 30 == 0:
            print(f"  event {i+1}/{len(events)}  ({time.time()-t0:.1f}s)")
        d = pd.Timestamp(ev["date"])
        if d not in returns.index:
            continue

        end_loc = returns.index.get_loc(d)
        window_pre = 15
        window_post = 5  # asymmetric: pre-event window matters more for prediction
        if end_loc < window_pre or end_loc + window_post >= len(returns):
            continue

        # Returns in window
        aapl_rets = returns["AAPL"].iloc[end_loc - window_pre:end_loc + window_post].dropna().to_numpy()
        xlk_rets = returns["XLK"].iloc[end_loc - window_pre:end_loc + window_post].dropna().to_numpy()

        # Wasserstein distance between the two return distributions
        if len(aapl_rets) >= 5 and len(xlk_rets) >= 5:
            w_dist = wasserstein_distance(aapl_rets, xlk_rets)
        else:
            w_dist = None

        # Wasserstein distance on |returns| (vol proxy)
        if len(aapl_rets) >= 5 and len(xlk_rets) >= 5:
            w_dist_abs = wasserstein_distance(np.abs(aapl_rets), np.abs(xlk_rets))
        else:
            w_dist_abs = None

        # Cross-correlation at each cascade order
        corr_per_order = {}
        for k in [1, 2, 3, 4]:
            aapl_s = aapl_z[k].iloc[end_loc - window_pre:end_loc + window_post].dropna().to_numpy()
            xlk_s = xlk_z[k].iloc[end_loc - window_pre:end_loc + window_post].dropna().to_numpy()
            min_len = min(len(aapl_s), len(xlk_s))
            if min_len >= 5:
                aapl_s = aapl_s[-min_len:]
                xlk_s = xlk_s[-min_len:]
                r, _ = sps.pearsonr(aapl_s, xlk_s)
                corr_per_order[k] = float(r)
            else:
                corr_per_order[k] = None

        # Derived metrics
        valid_corrs = {k: v for k, v in corr_per_order.items() if v is not None}
        corr_1 = corr_per_order.get(1)
        corr_2 = corr_per_order.get(2)
        corr_3 = corr_per_order.get(3)
        corr_4 = corr_per_order.get(4)
        # Slope of correlation across orders: high = correlation recovers at higher orders
        if all(c is not None for c in [corr_1, corr_2, corr_3, corr_4]):
            ks = [1, 2, 3, 4]
            cors = [corr_1, corr_2, corr_3, corr_4]
            slope, _, _, _, _ = sps.linregress(ks, cors)
            corr_slope = float(slope)
        else:
            corr_slope = None
        mean_corr = float(np.mean(list(valid_corrs.values()))) if valid_corrs else None

        records.append({
            "date": ev["date"],
            "label": ev["label"],
            "class": ev["class"],
            "asset": ev["asset"],
            "wasserstein_dist": w_dist,
            "wasserstein_dist_abs": w_dist_abs,
            "corr_1": corr_1, "corr_2": corr_per_order.get(2),
            "corr_3": corr_per_order.get(3), "corr_4": corr_4,
            "corr_slope": corr_slope,
            "mean_corr": mean_corr,
        })

    df = pd.DataFrame(records)
    print(f"\nanalyzed {len(df)} events")

    print("\n" + "=" * 78)
    print("RESULTS by event class")
    print("=" * 78)
    for cls in ["idiosyncratic", "systemic"]:
        sub = df[df["class"] == cls]
        if len(sub) == 0:
            continue
        print(f"\n  {cls} (n={len(sub)}):")
        for col in ["wasserstein_dist", "wasserstein_dist_abs",
                    "corr_1", "corr_4", "corr_slope", "mean_corr"]:
            valid = sub[col].dropna()
            if len(valid) > 0:
                print(f"    {col}: mean={valid.mean():.4f}, median={valid.median():.4f}")

    print("\n" + "=" * 78)
    print("CLASS DIFFERENTIATION TESTS")
    print("=" * 78)
    for col in ["wasserstein_dist", "wasserstein_dist_abs",
                "corr_1", "corr_2", "corr_3", "corr_4",
                "corr_slope", "mean_corr"]:
        idio = df[df["class"] == "idiosyncratic"][col].dropna()
        sys_ = df[df["class"] == "systemic"][col].dropna()
        if len(idio) > 5 and len(sys_) > 5:
            u, p = sps.mannwhitneyu(idio, sys_, alternative="two-sided")
            print(f"\n  {col}: idio median={idio.median():.4f}, sys median={sys_.median():.4f}, p={p:.4f}")
            # AUC
            labels = np.concatenate([np.ones(len(idio)), np.zeros(len(sys_))])
            scores = np.concatenate([idio.to_numpy(), sys_.to_numpy()])
            try:
                auc = roc_auc_score(labels, scores)
                print(f"    AUC (high {col} -> idiosyncratic) = {auc:.3f}")
            except Exception:
                pass

    out_path = RESULTS_DIR / "h3_ground_truth_v4.json"
    with open(out_path, "w") as f:
        json.dump({"events": records,
                   "summary": {
                       "n_total": int(len(df)),
                       "n_idiosyncratic": int((df["class"] == "idiosyncratic").sum()),
                       "n_systemic": int((df["class"] == "systemic").sum()),
                   }}, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
