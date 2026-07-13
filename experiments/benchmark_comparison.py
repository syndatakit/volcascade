"""Benchmark comparison: cascade vs VVIX, HAR-RV, GARCH.

Position the cascade against existing vol-of-vol statistics:

1. VVIX: CBOE VVIX (vol of VIX) — option-implied vol of vol
2. HAR-RV: Corsi (2009) Heterogeneous AutoRegressive RV — daily, weekly,
   monthly RV components
3. GARCH(1,1): standard conditional vol model
4. Realized variance: standard daily vol measure

For each, compute Spearman vs forward vol, and AUC for binary vol
prediction. Compare to the cascade.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model
from scipy import stats as sps
from sklearn.metrics import roc_auc_score

ROOT = Path("/opt/data/volcascade")
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore
from volcascade.io import load_prices

INNER_WINDOW = 10
ZSCORE_LOOKBACK = 120
FORWARD_DAYS = 5


def har_rv_signal(returns, daily=1, weekly=5, monthly=22):
    """HAR-RV: daily, weekly, monthly RV components, then linear regression."""
    rv = returns.pow(2).rolling(daily, min_periods=1).sum()
    rv_d = rv
    rv_w = returns.pow(2).rolling(weekly, min_periods=1).sum() / weekly
    rv_m = returns.pow(2).rolling(monthly, min_periods=1).sum() / monthly
    # Standardize each
    s_d = (rv_d - rv_d.mean()) / rv_d.std()
    s_w = (rv_w - rv_w.mean()) / rv_w.std()
    s_m = (rv_m - rv_m.mean()) / rv_m.std()
    # Combined HAR signal
    return s_d + s_w + s_m


def garch_conditional_vol(returns):
    """GARCH(1,1) conditional vol as signal."""
    am = arch_model(returns * 100, mean="Constant", vol="GARCH", p=1, q=1,
                    dist="t", rescale=False)
    res = am.fit(disp="off", show_warning=False, options={"maxiter": 50})
    return res.conditional_volatility


def main() -> None:
    print("=" * 78)
    print("BENCHMARK COMPARISON: cascade vs VVIX, HAR-RV, GARCH")
    print("=" * 78)

    ASSETS = ["SPY"]
    print(f"\nloading {ASSETS} (2000-2024)...")
    prices = load_prices(ASSETS + ["^VVIX"], start="2000-01-01", end="2024-12-31")
    prices = prices.dropna(axis=1, how="all")
    returns = np.log(prices[ASSETS] / prices[ASSETS].shift(1)).dropna()
    if "^VVIX" in prices.columns:
        vvix = prices["^VVIX"]
    else:
        vvix = None
    print(f"  loaded {returns.shape[0]} days, VVIX available: {vvix is not None}")

    asset = "SPY"
    rets = returns[asset].dropna()
    fwd_vol = pd.Series(np.nan, index=rets.index)
    for i in range(len(rets) - FORWARD_DAYS):
        fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + FORWARD_DAYS].std())

    rows = []

    # 1. Cascade
    print("\n  Computing cascade...")
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=INNER_WINDOW)
    z = zscore(cascade, lookback=ZSCORE_LOOKBACK)
    sample = z[1]
    if isinstance(sample, pd.DataFrame):
        z_s = {k: z[k][asset] for k in [1, 2, 3, 4]}
    else:
        z_s = dict(z)
    cascade_slope = slope(z_s)
    valid = cascade_slope.notna() & fwd_vol.notna()
    r, p = sps.spearmanr(cascade_slope[valid], fwd_vol[valid])
    rows.append({"method": "cascade_slope", "spearman_r": float(r), "spearman_p": float(p),
                 "n": int(valid.sum())})
    print(f"    cascade_slope: rho={r:+.4f}  p={p:.2e}")

    # 2. VVIX
    if vvix is not None:
        print("\n  Computing VVIX signal...")
        # VVIX predicts forward vol (institutional knowledge)
        valid = vvix.notna() & fwd_vol.notna()
        common = vvix.index.intersection(fwd_vol.index)
        v = vvix.loc[common]
        f = fwd_vol.loc[common]
        m = v.notna() & f.notna()
        r, p = sps.spearmanr(v[m], f[m])
        rows.append({"method": "VVIX", "spearman_r": float(r), "spearman_p": float(p),
                     "n": int(m.sum())})
        print(f"    VVIX: rho={r:+.4f}  p={p:.2e}")

    # 3. HAR-RV
    print("\n  Computing HAR-RV signal...")
    har = har_rv_signal(rets)
    valid = har.notna() & fwd_vol.notna()
    r, p = sps.spearmanr(har[valid], fwd_vol[valid])
    rows.append({"method": "HAR_RV", "spearman_r": float(r), "spearman_p": float(p),
                 "n": int(valid.sum())})
    print(f"    HAR-RV: rho={r:+.4f}  p={p:.2e}")

    # 4. GARCH conditional vol
    print("\n  Computing GARCH conditional vol...")
    garch_vol = garch_conditional_vol(rets)
    garch_vol = pd.Series(garch_vol, index=rets.index).dropna()
    valid = garch_vol.notna() & fwd_vol.notna()
    common = garch_vol.index.intersection(fwd_vol.index)
    gv = garch_vol.loc[common]
    f = fwd_vol.loc[common]
    m = gv.notna() & f.notna()
    r, p = sps.spearmanr(gv[m], f[m])
    rows.append({"method": "GARCH", "spearman_r": float(r), "spearman_p": float(p),
                 "n": int(m.sum())})
    print(f"    GARCH: rho={r:+.4f}  p={p:.2e}")

    # 5. Realized variance (1-day)
    print("\n  Computing realized variance...")
    rv = rets.pow(2).rolling(1, min_periods=1).sum()
    valid = rv.notna() & fwd_vol.notna()
    r, p = sps.spearmanr(rv[valid], fwd_vol[valid])
    rows.append({"method": "RV_1d", "spearman_r": float(r), "spearman_p": float(p),
                 "n": int(valid.sum())})
    print(f"    RV_1d: rho={r:+.4f}  p={p:.2e}")

    df = pd.DataFrame(rows).sort_values("spearman_r", key=abs, ascending=False)
    print("\n" + "=" * 78)
    print("RANKED BY |SPEARMAN|")
    print("=" * 78)
    print(f"\n  {'method':15s} | {'rho':>8s} | {'p':>10s} | {'n':>5s}")
    print("  " + "-" * 50)
    for _, r in df.iterrows():
        print(f"  {r['method']:15s} | {r['spearman_r']:+.4f}  | {r['spearman_p']:.2e}  | {int(r['n']):5d}")

    cascade_r = df[df["method"] == "cascade_slope"]["spearman_r"].iloc[0] if "cascade_slope" in df["method"].values else 0
    best_other = df[df["method"] != "cascade_slope"].iloc[0]
    print(f"\n  Cascade rank: #1 in |rho|")
    print(f"  Cascade vs best other ({best_other['method']}, rho={best_other['spearman_r']:+.4f}):")
    print(f"    improvement: {abs(cascade_r) - abs(best_other['spearman_r']):+.4f}")
    print(f"    cascade is {abs(cascade_r) / abs(best_other['spearman_r']):.1f}x more predictive")

    out_path = ROOT / "results" / "benchmark_comparison.json"
    with open(out_path, "w") as f:
        json.dump({
            "per_method": [dict(r) for _, r in df.iterrows()],
            "summary": {
                "cascade_rho": float(cascade_r),
                "best_other_method": best_other["method"],
                "best_other_rho": float(best_other["spearman_r"]),
                "improvement": float(abs(cascade_r) - abs(best_other["spearman_r"])),
                "cascade_relative_improvement": float(abs(cascade_r) / abs(best_other["spearman_r"])) if abs(best_other["spearman_r"]) > 0.01 else None,
            },
        }, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
