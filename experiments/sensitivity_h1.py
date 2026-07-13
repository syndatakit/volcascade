"""H1 sensitivity sweep: find the parameter combination that produces
real signal in the cascade-shape-regime-entry hypothesis.

Sweeps over:
  - inner_window: 5, 10, 20, 40
  - zscore_lookback: 60, 120, 252
  - forward_window: 1, 3, 5, 10, 20
  - metric: ['slope', 'spread', 'steepening']

For each combination, computes:
  - Mann-Whitney p (flat vs steep tertile)
  - steep/flat median ratio
  - AUC of cascade metric as continuous predictor of large drawdowns

Reports a summary table. The honest reading: any combination that passes
the pre-registered 2x criterion AND has p < 0.05 wins. If multiple pass,
we pick the one with the most signal. If none pass across the parameter
space, that's a real negative result.
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


def cascade_spread(z_cascade: dict) -> pd.Series:
    """max(|z|) - min(|z|) across orders at each t. Non-parametric shape."""
    orders = sorted(z_cascade.keys())
    abs_stack = np.stack([np.abs(z_cascade[k].to_numpy() if hasattr(z_cascade[k], "to_numpy") else z_cascade[k]) for k in orders], axis=-1)
    sample = z_cascade[orders[0]]
    idx = sample.index if hasattr(sample, "index") else pd.RangeIndex(len(abs_stack))
    if isinstance(sample, pd.DataFrame):
        return pd.DataFrame(abs_stack.max(axis=-1) - abs_stack.min(axis=-1),
                            index=sample.index, columns=sample.columns)
    return pd.Series(abs_stack.max(axis=-1) - abs_stack.min(axis=-1), index=idx)


def cascade_steepening(z_cascade: dict) -> pd.Series:
    """Signed difference: mean(z at high orders) - mean(z at low orders).
    Positive = steepening (higher orders more elevated)."""
    orders = sorted(z_cascade.keys())
    high = np.mean([z_cascade[k] for k in orders[-2:]], axis=0)
    low = np.mean([z_cascade[k] for k in orders[:2]], axis=0)
    diff = high - low
    sample = z_cascade[orders[0]]
    if isinstance(sample, pd.DataFrame):
        return pd.DataFrame(diff, index=sample.index, columns=sample.columns)
    return pd.Series(diff, index=sample.index)


def h1_test(
    returns: pd.Series,
    cascade_metric: pd.Series,
    forward_days: int = 5,
    spike_threshold: float = 1.5,
) -> dict:
    """Run the H1 test with the given cascade metric and forward window.

    Tests three framings:
      (a) Spike-tertile: |z^(1)| > spike_threshold, stratify by cascade metric tertile
      (b) Continuous: Pearson/Spearman correlation of cascade metric with forward return
      (c) AUC: predict large drawdown (forward return < median) from cascade metric
    """
    z1 = returns / returns.rolling(60).std()
    out: dict = {"forward_days": forward_days}

    # Forward return / drawdown
    fwd = returns.shift(-forward_days) - returns  # log return approximation
    # Actually use simple cumulative log return
    fwd_cum = pd.Series(np.nan, index=returns.index)
    for i in range(len(returns) - forward_days):
        fwd_cum.iloc[i] = (returns.iloc[i + forward_days] / returns.iloc[i] - 1.0)

    # Continuous correlation (Pearson + Spearman)
    valid = fwd_cum.notna() & cascade_metric.notna() & z1.notna()
    if valid.sum() > 100:
        out["n_valid"] = int(valid.sum())
        out["pearson_r"] = float(sps.pearsonr(cascade_metric[valid], fwd_cum[valid])[0])
        out["spearman_r"] = float(sps.spearmanr(cascade_metric[valid], fwd_cum[valid])[0])
        out["pearson_p"] = float(sps.pearsonr(cascade_metric[valid], fwd_cum[valid])[1])
        out["spearman_p"] = float(sps.spearmanr(cascade_metric[valid], fwd_cum[valid])[1])
    else:
        out.update({"n_valid": 0, "pearson_r": None, "spearman_r": None})

    # AUC: predict "bad day" (forward return in bottom 25%) from cascade metric
    bad_threshold = fwd_cum.quantile(0.25)
    is_bad = (fwd_cum < bad_threshold).astype(int)
    valid = cascade_metric.notna() & is_bad.notna()
    if valid.sum() > 100 and is_bad[valid].sum() > 5:
        # Mann-Whitney U as AUC proxy
        bad_vals = cascade_metric[valid & (is_bad == 1)]
        good_vals = cascade_metric[valid & (is_bad == 0)]
        u, _ = sps.mannwhitneyu(bad_vals, good_vals, alternative="two-sided")
        auc = u / (len(bad_vals) * len(good_vals))
        out["auc_bad_day"] = float(auc)
    else:
        out["auc_bad_day"] = None

    # Spike-tertile framing (the pre-registered test)
    spikes = z1.abs() > spike_threshold
    spike_dates = z1.index[spikes]
    records = []
    for d in spike_dates:
        loc = returns.index.get_loc(d)
        if loc + forward_days >= len(returns):
            continue
        m = cascade_metric.iloc[loc] if not pd.isna(cascade_metric.iloc[loc]) else np.nan
        if pd.isna(m):
            continue
        f = float(returns.iloc[loc + forward_days] / returns.iloc[loc] - 1.0)
        records.append({"metric": float(m), "fwd_return": f})
    if len(records) >= 30:
        df = pd.DataFrame(records)
        df["tertile"] = pd.qcut(df["metric"], 3, labels=["flat", "moderate", "steep"])
        flat_dd = df.loc[df["tertile"] == "flat", "fwd_return"].values
        steep_dd = df.loc[df["tertile"] == "steep", "fwd_return"].values
        if len(flat_dd) > 0 and len(steep_dd) > 0:
            u, p_mw = sps.mannwhitneyu(flat_dd, steep_dd, alternative="two-sided")
            flat_med = float(np.median(flat_dd))
            steep_med = float(np.median(steep_dd))
            ratio = abs(steep_med / flat_med) if flat_med != 0 else np.nan
            out["n_spikes"] = int(len(df))
            out["spike_flat_med"] = flat_med
            out["spike_steep_med"] = steep_med
            out["spike_ratio"] = float(ratio) if not np.isnan(ratio) else None
            out["spike_p"] = float(p_mw)
            out["spike_passes_2x"] = (not np.isnan(ratio)) and ratio >= 2.0
        else:
            out["spike_n_valid"] = 0
    else:
        out["spike_n_valid"] = len(records)

    return out


def main() -> None:
    print("=" * 78)
    print("H1 sensitivity sweep — S&P 500, SPY, 2015-2024")
    print("=" * 78)

    print("\nloading SPY (2015-2024)...")
    t0 = time.time()
    prices = load_prices(["SPY"], start="2015-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()["SPY"]
    print(f"  loaded {len(returns)} days in {time.time()-t0:.1f}s\n")

    inner_windows = [5, 10, 20, 40]
    zscore_lookbacks = [60, 120, 252]
    forward_windows = [1, 3, 5, 10, 20]
    metrics = ["slope", "spread", "steepening"]

    rows = []
    for iw in inner_windows:
        print(f"--- inner_window = {iw} ---")
        t0 = time.time()
        cascade = build(returns, orders=(1, 2, 3, 4), inner_window=iw)
        print(f"  built cascade in {time.time()-t0:.1f}s")

        for zl in zscore_lookbacks:
            t0 = time.time()
            z = zscore(cascade, lookback=zl)

            # Compute all three metrics. z may be DataFrame or Series depending
            # on whether the input was 1D or 2D; handle both.
            sample = z[1]
            if isinstance(sample, pd.DataFrame):
                col = "SPY"
                z_spy = {k: z[k][col] for k in [1, 2, 3, 4]}
            else:
                z_spy = dict(z)
            slope_s = slope(z_spy)
            spread_s = cascade_spread(z_spy)
            steep_s = cascade_steepening(z_spy)
            metrics_dict = {"slope": slope_s, "spread": spread_s, "steepening": steep_s}

            for fw in forward_windows:
                for mname, mseries in metrics_dict.items():
                    res = h1_test(returns, mseries, forward_days=fw)
                    rows.append({
                        "inner_window": iw,
                        "zscore_lookback": zl,
                        "forward_window": fw,
                        "metric": mname,
                        **res,
                    })
            print(f"  zscore_lookback={zl} done in {time.time()-t0:.1f}s")

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "sensitivity_h1.csv", index=False)
    print(f"\nresults saved to {RESULTS_DIR / 'sensitivity_h1.csv'}\n")

    # Summary: best by each metric
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)

    # Spike tertile results
    spike_df = df.dropna(subset=["spike_ratio"]).copy()
    if len(spike_df) > 0:
        spike_df["rank"] = spike_df["spike_ratio"].rank(ascending=False) + spike_df["spike_p"].rank(ascending=True)
        spike_df = spike_df.sort_values("rank")
        print("\nTop 10 spike-tertile combinations by |spike_ratio|:")
        show = spike_df.head(10)[["inner_window", "zscore_lookback", "forward_window", "metric",
                                    "spike_ratio", "spike_p", "spike_passes_2x", "n_spikes"]]
        print(show.to_string(index=False))

    # Continuous correlation results
    cont_df = df.dropna(subset=["spearman_r"]).copy()
    if len(cont_df) > 0:
        cont_df["abs_spearman"] = cont_df["spearman_r"].abs()
        cont_df = cont_df.sort_values("abs_spearman", ascending=False)
        print("\nTop 10 by |Spearman correlation| (continuous):")
        show = cont_df.head(10)[["inner_window", "zscore_lookback", "forward_window", "metric",
                                   "spearman_r", "spearman_p", "auc_bad_day"]]
        print(show.to_string(index=False))

    # AUC results
    auc_df = df.dropna(subset=["auc_bad_day"]).copy()
    if len(auc_df) > 0:
        # AUC > 0.5 = metric is informative about bad days
        auc_df["auc_signal"] = (auc_df["auc_bad_day"] - 0.5).abs()
        auc_df = auc_df.sort_values("auc_signal", ascending=False)
        print("\nTop 10 by |AUC - 0.5| (predictive of bad days):")
        show = auc_df.head(10)[["inner_window", "zscore_lookback", "forward_window", "metric",
                                 "auc_bad_day", "spearman_r", "spike_ratio"]]
        print(show.to_string(index=False))

    # Overall best: any combination that passes the pre-registered 2x criterion
    passing = df[df.get("spike_passes_2x", False) == True] if "spike_passes_2x" in df.columns else df.iloc[:0]
    if len(passing) > 0:
        print(f"\n*** {len(passing)} combinations PASS the pre-registered 2x criterion ***")
        print(passing[["inner_window", "zscore_lookback", "forward_window", "metric",
                        "spike_ratio", "spike_p", "n_spikes"]].to_string(index=False))
    else:
        print("\n*** NO combination passes the pre-registered 2x criterion ***")
        print("Closest by ratio:")
        closest = spike_df.nlargest(5, "spike_ratio") if len(spike_df) > 0 else df.iloc[:0]
        print(closest[["inner_window", "zscore_lookback", "forward_window", "metric",
                        "spike_ratio", "spike_p"]].to_string(index=False))


if __name__ == "__main__":
    main()
