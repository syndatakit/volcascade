"""Adversarial test for the vol-peak finding.

RQs will say "is this just vol-of-vol with extra steps?" The rebuttal
rests on: iid N(0, sigma^2) returns should produce NO correlation
between cascade slope and forward realized vol.

For 1000 independent synthetic universes of iid returns, compute:
- Pearson and Spearman correlation of cascade slope with forward 5-day vol
- Distribution of the correlations across the 1000 universes
- Expected: |rho| < 0.05 in 95%+ of universes
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

RESULTS_DIR = ROOT / "results"


def main() -> None:
    print("=" * 78)
    print("Adversarial test: iid returns -> no spurious vol-peak signal")
    print("=" * 78)

    n_universes = 1000
    n_days = 5000
    inner_window = 10
    zscore_lookback = 120
    forward_days = 5

    r_pearson = np.zeros(n_universes)
    r_spearman = np.zeros(n_universes)
    p_pearson = np.zeros(n_universes)
    p_spearman = np.zeros(n_universes)

    rng = np.random.default_rng(42)
    t0 = time.time()
    for k in range(n_universes):
        if (k + 1) % 100 == 0:
            print(f"  universe {k+1}/{n_universes}  ({time.time()-t0:.1f}s)")
        rets = pd.Series(rng.normal(0, 0.01, n_days))
        cascade = build(rets, orders=(1, 2, 3, 4), inner_window=inner_window)
        z = zscore(cascade, lookback=zscore_lookback)
        s = slope(z).dropna()

        fwd_vol = pd.Series(np.nan, index=rets.index)
        for i in range(len(rets) - forward_days):
            fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + forward_days].std())

        valid = s.notna() & fwd_vol.notna()
        if valid.sum() < 100:
            continue
        r_p, p_p = sps.pearsonr(s[valid], fwd_vol[valid])
        r_s, p_s = sps.spearmanr(s[valid], fwd_vol[valid])
        r_pearson[k] = r_p
        r_spearman[k] = r_s
        p_pearson[k] = p_p
        p_spearman[k] = p_s

    elapsed = time.time() - t0
    print(f"\ndone: {n_universes} universes in {elapsed:.1f}s")
    print(f"  Pearson  rho: mean={r_pearson.mean():+.4f}  std={r_pearson.std():.4f}  "
          f"|rho| > 0.05: {(np.abs(r_pearson) > 0.05).sum() / n_universes:.1%}")
    print(f"  Spearman rho: mean={r_spearman.mean():+.4f}  std={r_spearman.std():.4f}  "
          f"|rho| > 0.05: {(np.abs(r_spearman) > 0.05).sum() / n_universes:.1%}")
    print(f"  Pearson  p < 0.05: {(p_pearson < 0.05).sum() / n_universes:.1%}  (expected ~5% if no signal)")
    print(f"  Spearman p < 0.05: {(p_spearman < 0.05).sum() / n_universes:.1%}  (expected ~5% if no signal)")

    # Save results
    out = {
        "n_universes": n_universes,
        "n_days": n_days,
        "params": {"inner_window": inner_window, "zscore_lookback": zscore_lookback, "forward_days": forward_days},
        "pearson": {
            "mean": float(r_pearson.mean()),
            "std": float(r_pearson.std()),
            "frac_abs_gt_005": float((np.abs(r_pearson) > 0.05).mean()),
            "frac_p_lt_005": float((p_pearson < 0.05).mean()),
        },
        "spearman": {
            "mean": float(r_spearman.mean()),
            "std": float(r_spearman.std()),
            "frac_abs_gt_005": float((np.abs(r_spearman) > 0.05).mean()),
            "frac_p_lt_005": float((p_spearman < 0.05).mean()),
        },
    }
    out_path = RESULTS_DIR / "adversarial_vol_peak.json"
    with open(out_path, "w") as f:
        import json
        json.dump(out, f, indent=2)
    print(f"\nresults saved to {out_path}")
    print("PASS criterion: |Spearman rho| < 0.05 in 95%+ of universes (i.e. no signal on noise)")
    verdict = "PASS" if (np.abs(r_spearman) > 0.05).mean() < 0.05 else "FAIL"
    print(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
