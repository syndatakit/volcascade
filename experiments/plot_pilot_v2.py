"""Generate diagnostic plots for the vol-peak finding (pilot v2)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore  # noqa: E402
from volcascade.io import SP500_SECTOR_ETFS, load_prices  # noqa: E402

RESULTS_DIR = ROOT / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)


def main() -> None:
    print("generating vol-peak diagnostic plots...")

    # Load data
    prices = load_prices(list(SP500_SECTOR_ETFS), start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()

    # Compute cascade + slope for SPY
    rets = returns["SPY"].dropna()
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=10)
    z = zscore(cascade, lookback=120)
    sample = z[1]
    if isinstance(sample, pd.DataFrame):
        z_spy = {k: z[k]["SPY"] for k in [1, 2, 3, 4]}
    else:
        z_spy = dict(z)
    s = slope(z_spy).dropna()

    # Forward realized vol
    fwd_vol = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - 5):
        fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + 5].std())

    # Forward return
    fwd_ret = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - 5):
        fwd_ret.iloc[i] = float(rets.iloc[i + 5] / rets.iloc[i] - 1.0)

    # 1. Time series plot: cascade slope (top) + forward vol (bottom)
    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)

    # Top: cascade slope
    ax = axes[0]
    ax.plot(s.index, s.values, linewidth=0.5, color="black", alpha=0.8)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_ylabel("cascade slope β")
    ax.set_title("SPY 2000-2024: cascade slope predicts forward vol, not forward return")
    ax.grid(True, alpha=0.3)

    # Middle: forward realized vol
    ax = axes[1]
    fwd_vol_clean = fwd_vol.dropna()
    ax.plot(fwd_vol_clean.index, fwd_vol_clean.values * np.sqrt(252), linewidth=0.5, color="steelblue", alpha=0.7)
    ax.set_ylabel("forward 5-day vol\n(annualized)")
    ax.grid(True, alpha=0.3)

    # Bottom: forward return
    ax = axes[2]
    fwd_ret_clean = fwd_ret.dropna()
    ax.plot(fwd_ret_clean.index, fwd_ret_clean.values * 100, linewidth=0.5, color="darkred", alpha=0.7)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_ylabel("forward 5-day return (%)")
    ax.set_xlabel("date")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out = PLOTS_DIR / "cascade_vs_forward_outcomes.png"
    fig.savefig(out, dpi=100)
    print(f"  wrote {out}")
    plt.close(fig)

    # 2. Binned scatter: average forward vol by cascade slope quintile
    valid = s.notna() & fwd_vol.notna()
    df = pd.DataFrame({"slope": s[valid], "fwd_vol": fwd_vol[valid]})
    df["quintile"] = pd.qcut(df["slope"], 5, labels=False)

    grouped = df.groupby("quintile").agg(
        slope_mid=("slope", "median"),
        fwd_vol_mean=("fwd_vol", "mean"),
        fwd_vol_std=("fwd_vol", "std"),
        n=("slope", "count"),
    )
    grouped["fwd_vol_se"] = grouped["fwd_vol_std"] / np.sqrt(grouped["n"])
    grouped["fwd_vol_annualized"] = grouped["fwd_vol_mean"] * np.sqrt(252)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.errorbar(grouped["slope_mid"], grouped["fwd_vol_annualized"],
                yerr=grouped["fwd_vol_se"] * np.sqrt(252),
                fmt="o-", color="steelblue", linewidth=2, markersize=8, capsize=4)
    ax.set_xlabel("cascade slope β (quintile median)")
    ax.set_ylabel("forward 5-day realized vol (annualized)")
    ax.set_title("Forward vol by cascade slope quintile (SPY 2000-2024)\n"
                 "higher slope → lower forward vol (vol exhaustion effect)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = PLOTS_DIR / "forward_vol_by_slope_quintile.png"
    fig.savefig(out, dpi=100)
    print(f"  wrote {out}")
    plt.close(fig)

    # 3. Per-asset Spearman bar plot
    with open(RESULTS_DIR / "pilot_v2_vol_peak.json") as f:
        results = json.load(f)["per_asset"]
    df_assets = pd.DataFrame(results)

    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(df_assets))
    width = 0.35
    ax.bar(x - width/2, df_assets["forward_vol_spearman_r"], width,
           label="slope → forward vol", color="steelblue", alpha=0.8)
    ax.bar(x + width/2, df_assets["forward_return_spearman_r"], width,
           label="slope → forward return", color="darkred", alpha=0.8)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(df_assets["asset"], rotation=45, ha="right")
    ax.set_ylabel("Spearman correlation")
    ax.set_title("Cascade slope predictive power by asset (12 sector ETFs, 2000-2024)\n"
                 "vol signal is consistently negative; return signal is near zero")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    out = PLOTS_DIR / "spearman_by_asset.png"
    fig.savefig(out, dpi=100)
    print(f"  wrote {out}")
    plt.close(fig)

    print("done.")


if __name__ == "__main__":
    main()
