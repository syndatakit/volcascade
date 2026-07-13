"""Generate diagnostic plots from the S&P 500 pilot results.

Reads results/pilot_spy.json and produces:
- slope_spy.png: cascade slope time series for SPY with crisis overlays
- forward_dd_by_tertile.png: histogram of forward 5-day returns by slope tertile
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for sandbox
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from volcascade.io import load_prices  # noqa: E402

RESULTS_DIR = ROOT / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)


def plot_slope_spy() -> None:
    """Plot SPY cascade slope with crisis events overlaid."""
    prices = load_prices(["SPY"], start="2015-01-01", end="2024-12-31")
    from volcascade import build, slope, zscore
    returns = np.log(prices / prices.shift(1)).dropna()
    cascade = build(returns, orders=(1, 2, 3, 4), inner_window=20)
    z = zscore(cascade, lookback=120)
    s = slope({k: z[k]["SPY"] for k in [1, 2, 3, 4]}).dropna()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(s.index, s.values, linewidth=0.6, color="black", alpha=0.8)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")

    # Overlay global crisis events
    crises = [
        ("2015-08-24", "China devaluation"),
        ("2018-12-24", "Christmas Eve"),
        ("2020-03-16", "COVID peak"),
        ("2022-02-24", "Russia-Ukraine"),
    ]
    for d, label in crises:
        ts = pd.Timestamp(d)
        if ts >= s.index[0] and ts <= s.index[-1]:
            ax.axvline(ts, color="red", linewidth=0.8, alpha=0.5)
            ax.text(ts, ax.get_ylim()[1] * 0.9, label, rotation=90,
                    fontsize=7, color="red", va="top", ha="right")

    ax.set_ylabel("cascade slope β")
    ax.set_xlabel("date")
    ax.set_title("SPY volatility cascade slope (2015-2024)\n"
                 "with global crisis events overlaid")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = PLOTS_DIR / "slope_spy.png"
    fig.savefig(out, dpi=100)
    print(f"  wrote {out}")
    plt.close(fig)


def plot_forward_dd_by_tertile() -> None:
    """Histogram of forward 5-day returns by slope tertile, from H1 results."""
    with open(RESULTS_DIR / "pilot_spy.json") as f:
        results = json.load(f)
    h1 = results["H1_spike_drawdown"]
    if h1.get("status") != "ok":
        print("  H1 did not produce results; skipping dd plot")
        return

    # We don't have the raw spike records in the JSON (only the summary),
    # so we re-run a quick H1 to get the per-spike records
    prices = load_prices(["SPY"], start="2015-01-01", end="2024-12-31")
    from volcascade import build, slope, zscore
    returns = np.log(prices / prices.shift(1)).dropna()
    cascade = build(returns, orders=(1, 2, 3, 4), inner_window=20)
    z = zscore(cascade, lookback=120)
    s = slope({k: z[k]["SPY"] for k in [1, 2, 3, 4]})

    z1 = returns["SPY"] / returns["SPY"].rolling(60).std()
    spikes = z1.abs() > 1.5
    spike_dates = z1.index[spikes]

    records = []
    for d in spike_dates:
        loc = returns.index.get_loc(d)
        if loc + 5 >= len(returns):
            continue
        slope_val = s.iloc[loc]
        if pd.isna(slope_val):
            continue
        fwd = float(returns["SPY"].iloc[loc + 5] / returns["SPY"].iloc[loc] - 1.0)
        records.append({"slope": float(slope_val), "fwd": fwd})
    df = pd.DataFrame(records)
    df["tertile"] = pd.qcut(df["slope"], 3, labels=["flat", "moderate", "steep"])

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = {"flat": "#1f77b4", "moderate": "#7f7f7f", "steep": "#d62728"}
    for tert in ["flat", "moderate", "steep"]:
        sub = df.loc[df["tertile"] == tert, "fwd"]
        ax.hist(sub, bins=30, alpha=0.5, label=f"{tert} (n={len(sub)})", color=colors[tert])
    ax.axvline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel("forward 5-day return")
    ax.set_ylabel("count")
    ax.set_title("Forward 5-day return distribution by cascade slope tertile\n"
                 f"SPY 2015-2024, {len(df)} order-1 spike events")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = PLOTS_DIR / "forward_dd_by_tertile.png"
    fig.savefig(out, dpi=100)
    print(f"  wrote {out}")
    plt.close(fig)


def main() -> None:
    print("generating diagnostic plots...")
    plot_slope_spy()
    plot_forward_dd_by_tertile()
    print("done.")


if __name__ == "__main__":
    main()
