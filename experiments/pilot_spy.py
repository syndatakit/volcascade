"""Pilot: H1 (regime entry) and H3 (cross-sectional decoupling) on S&P 500.

Loads SPY + 11 SPDR sector ETFs + a single stock (AAPL) for the H3
test, constructs the volatility cascade, and runs the headline H1 and
H3 analyses defined in docs/METHODOLOGY.md.

Results are written to results/pilot_spy.json (machine-readable) and
results/pilot_spy_summary.md (human-readable).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore  # noqa: E402
from volcascade.baselines import hmm_regime  # noqa: E402
from volcascade.decoupling import chow_decoupling  # noqa: E402
from volcascade.io import GLOBAL_CRISES, SP500_SECTOR_ETFS, load_prices  # noqa: E402

RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def h1_forward_drawdown(
    returns: pd.Series, slope_series: pd.Series, forward_days: int = 5
) -> dict:
    """H1: classify order-1 spike events by cascade-slope tertile, compare forward drawdowns.

    A spike event is any day with |z^(1)| > 1.5. For each spike, record
    the cascade slope at that day and the forward 5-day drawdown. Then
    stratify by slope tertile (flat / moderate / steep) and test whether
    the steep-tertile spikes have larger forward drawdowns.

    Pre-registered pass criterion (DESIGN_MEMO.md): steep-tertile spikes
    have >= 2x the median forward 5-day drawdown of flat-tertile spikes.
    """
    z1 = returns / returns.rolling(60).std()
    spikes = z1.abs() > 1.5
    spike_dates = z1.index[spikes]

    if len(spike_dates) < 30:
        return {"status": "insufficient_spikes", "n_spikes": int(len(spike_dates))}

    # For each spike, record the slope and the forward N-day drawdown
    records = []
    for d in spike_dates:
        loc = returns.index.get_loc(d)
        if loc + forward_days >= len(returns):
            continue
        # Cascade slope at the spike
        s = slope_series.iloc[loc] if not pd.isna(slope_series.iloc[loc]) else np.nan
        if pd.isna(s):
            continue
        # Forward N-day return (negative = drawdown)
        fwd = (returns.iloc[loc + forward_days] / returns.iloc[loc] - 1.0)
        records.append({"date": str(d.date()), "slope": float(s), "fwd_return": float(fwd)})

    df = pd.DataFrame(records)
    if len(df) < 30:
        return {"status": "insufficient_valid_spikes", "n_valid": len(df)}

    # Stratify by slope tertile
    df["slope_tertile"] = pd.qcut(df["slope"], 3, labels=["flat", "moderate", "steep"])

    # Median forward return (more negative = larger drawdown) per tertile
    grouped = df.groupby("slope_tertile", observed=True)["fwd_return"].agg(
        ["count", "median", "mean", "std"]
    )

    # Statistical test: Mann-Whitney U (two-sided), steep vs flat
    flat_dd = df.loc[df["slope_tertile"] == "flat", "fwd_return"].values
    steep_dd = df.loc[df["slope_tertile"] == "steep", "fwd_return"].values
    if len(flat_dd) > 0 and len(steep_dd) > 0:
        u, p_mw = sps.mannwhitneyu(flat_dd, steep_dd, alternative="two-sided")
    else:
        u, p_mw = np.nan, np.nan

    # Pre-registered success criterion: |steep median| / |flat median| >= 2
    flat_med = float(grouped.loc["flat", "median"]) if "flat" in grouped.index else np.nan
    steep_med = float(grouped.loc["steep", "median"]) if "steep" in grouped.index else np.nan
    ratio = abs(steep_med / flat_med) if (flat_med != 0 and not np.isnan(flat_med)) else np.nan
    passes = (not np.isnan(ratio)) and ratio >= 2.0

    return {
        "status": "ok",
        "n_spikes": int(len(df)),
        "n_flat": int(len(flat_dd)),
        "n_steep": int(len(steep_dd)),
        "flat_median_fwd_return": flat_med,
        "steep_median_fwd_return": steep_med,
        "steep_to_flat_ratio": float(ratio) if not np.isnan(ratio) else None,
        "mannwhitney_U": float(u) if not np.isnan(u) else None,
        "mannwhitney_p": float(p_mw) if not np.isnan(p_mw) else None,
        "passes_2x_criterion": bool(passes),
        "all_tertile_stats": grouped.to_dict(),
    }


def h3_aapl_xlk_decoupling(
    aapl_z: dict, xlk_z: dict, lookback: int = 100, alpha: float = 0.05
) -> dict:
    """H3: Chow-test decoupling for AAPL vs XLK at each cascade order.

    The decoupling order is the smallest k at which the sliding-window
    Chow test rejects the null of stable stock-sector conditional
    distributions. Each order uses that order's z-scored series for the
    stock and sector.
    """
    per_order = {}
    decoupling_order: int | None = None
    for k in [1, 2, 3, 4]:
        if k not in aapl_z or k not in xlk_z:
            continue
        s = aapl_z[k]["AAPL"].dropna()
        x = xlk_z[k]["XLK"].dropna()
        # Align on common dates
        common = s.index.intersection(x.index)
        s = s.loc[common]
        x = x.loc[common]
        out = chow_decoupling(
            s, x, max_order=1, lookback=lookback, alpha=alpha
        )
        per_order[k] = {
            "max_F": float(out["f_statistics"][1][0]),
            "min_p": float(out["f_statistics"][1][1]),
            "decoupling_detected": (out["f_statistics"][1][1] < alpha),
        }
        if decoupling_order is None and per_order[k]["decoupling_detected"]:
            decoupling_order = k

    return {
        "decoupling_order": decoupling_order,
        "co_moves": decoupling_order is None,
        "f_statistics_per_order": per_order,
    }


def main() -> None:
    print("=" * 70)
    print("volcascade pilot — S&P 500 + sector ETFs")
    print("=" * 70)

    # 1. Load data
    print("\n[1/5] loading SPY + 11 sector ETFs (2015-01-01 to 2024-12-31)...")
    t0 = time.time()
    sector_tickers = list(SP500_SECTOR_ETFS)
    prices = load_prices(sector_tickers, start="2015-01-01", end="2024-12-31")
    print(f"      loaded {prices.shape[0]} trading days x {prices.shape[1]} tickers in {time.time()-t0:.1f}s")
    print(f"      columns: {list(prices.columns)}")

    # 2. Build cascade
    print("\n[2/5] building cascade (orders 1-4, inner_window=20)...")
    t0 = time.time()
    returns = np.log(prices / prices.shift(1)).dropna()
    cascade = build(returns, orders=(1, 2, 3, 4), inner_window=20)
    print(f"      done in {time.time()-t0:.1f}s")
    for k, c in cascade.items():
        n_valid = c.dropna(how="all").shape[0]
        print(f"      order {k}: {n_valid} valid days")

    # 3. Z-score and slope
    print("\n[3/5] z-scoring (lookback=120) and computing cascade slope...")
    t0 = time.time()
    z = zscore(cascade, lookback=120)
    # Slope on the broad market (SPY) for H1
    slope_spy = slope({k: z[k]["SPY"] for k in [1, 2, 3, 4]})
    print(f"      done in {time.time()-t0:.1f}s")
    print(f"      slope range: [{slope_spy.min():.3f}, {slope_spy.max():.3f}]")
    print(f"      slope mean: {slope_spy.mean():.3f}, std: {slope_spy.std():.3f}")

    # 4. H1: forward drawdown by slope tertile
    print("\n[4/5] H1: forward 5-day drawdown by slope tertile (SPY)...")
    t0 = time.time()
    h1 = h1_forward_drawdown(returns["SPY"], slope_spy, forward_days=5)
    print(f"      done in {time.time()-t0:.1f}s")
    if h1.get("status") == "ok":
        print(f"      n_spikes = {h1['n_spikes']}")
        print(f"      flat-tertile median fwd return: {h1['flat_median_fwd_return']:.4f}")
        print(f"      steep-tertile median fwd return: {h1['steep_median_fwd_return']:.4f}")
        print(f"      steep/flat ratio: {h1['steep_to_flat_ratio']:.2f}x")
        print(f"      Mann-Whitney p: {h1['mannwhitney_p']:.4f}")
        print(f"      passes 2x criterion: {h1['passes_2x_criterion']}")
    else:
        print(f"      status: {h1}")

    # 5. H3: AAPL vs XLK decoupling
    print("\n[5/5] H3: AAPL vs XLK decoupling (Chow test, sliding window)...")
    t0 = time.time()
    try:
        aapl_prices = load_prices(["AAPL", "XLK"], start="2015-01-01", end="2024-12-31")
        aapl_returns = np.log(aapl_prices / aapl_prices.shift(1)).dropna()
        aapl_cascade = build(aapl_returns, orders=(1, 2, 3, 4), inner_window=20)
        aapl_z = zscore(aapl_cascade, lookback=120)
        h3 = h3_aapl_xlk_decoupling(aapl_z, aapl_z, lookback=100)
    except Exception as e:
        h3 = {"status": "error", "error": str(e)}
    print(f"      done in {time.time()-t0:.1f}s")
    if "decoupling_order" in h3:
        print(f"      decoupling_order: {h3['decoupling_order']}")
        print(f"      co_moves: {h3['co_moves']}")
        for k, v in h3["f_statistics_per_order"].items():
            print(f"      order {k}: max_F={v['max_F']:.2f}, min_p={v['min_p']:.6f}, decoupling={v['decoupling_detected']}")
    else:
        print(f"      status: {h3}")

    # Save results
    out = {
        "data": {
            "tickers": list(prices.columns),
            "n_days": int(prices.shape[0]),
            "date_range": [str(prices.index[0].date()), str(prices.index[-1].date())],
        },
        "cascade": {
            "orders": [1, 2, 3, 4],
            "inner_window": 20,
            "zscore_lookback": 120,
        },
        "slope_spy": {
            "mean": float(slope_spy.mean()),
            "std": float(slope_spy.std()),
            "min": float(slope_spy.min()),
            "max": float(slope_spy.max()),
        },
        "H1_spike_drawdown": h1,
        "H3_aapl_xlk": h3,
        "ground_truth_global_crises": GLOBAL_CRISES,
    }
    out_path = RESULTS_DIR / "pilot_spy.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nresults written to {out_path}")


if __name__ == "__main__":
    main()
