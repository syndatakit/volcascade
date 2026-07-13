"""GARCH-residual test for H3b (event magnitude prediction).

The H3b finding (cascade slope at event day -> |return| on event day,
Spearman -0.33) might be GARCH-driven, similar to the vol-peak effect.

This test:
1. Fit GARCH(1,1) to AAPL, XLK, SPY.
2. Compute standardized residuals for each.
3. Apply the cascade to the RESIDUALS.
4. Test if cascade slope at event day predicts |residual| on event day.

If the magnitude effect PERSISTS on GARCH-residuals, the H3b finding
is genuinely beyond GARCH (and thus a stronger result). If it
DISAPPEARS, the magnitude effect is also mostly GARCH-driven (and we
need to add that caveat to the paper).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from volcascade import build, slope, zscore  # noqa: E402
from volcascade.io import load_prices  # noqa: E402
from h3_ground_truth import aapl_earnings_dates, fomc_dates  # noqa: E402

RESULTS_DIR = ROOT / "results"


def garch_residuals(rets: pd.Series) -> pd.Series:
    am = arch_model(rets * 100, mean="Constant", vol="GARCH", p=1, q=1,
                    dist="t", rescale=False)
    res = am.fit(disp="off", show_warning=False, options={"maxiter": 50})
    return res.std_resid.dropna()


def main() -> None:
    print("=" * 78)
    print("H3b GARCH-residual test: does event magnitude effect persist?")
    print("=" * 78)

    events = aapl_earnings_dates() + fomc_dates()
    print(f"\n{len(events)} curated events")

    print("\nloading AAPL, XLK, SPY (2015-2024)...")
    t0 = time.time()
    prices = load_prices(["AAPL", "XLK", "SPY"], start="2015-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    # Compute GARCH residuals
    print("computing GARCH residuals...")
    t0 = time.time()
    aapl_resid = garch_residuals(returns["AAPL"])
    xlk_resid = garch_residuals(returns["XLK"])
    spy_resid = garch_residuals(returns["SPY"])
    print(f"  GARCH done in {time.time()-t0:.1f}s\n")

    # Cascade on residuals
    aapl_cascade = build(aapl_resid, orders=(1, 2, 3, 4), inner_window=10)
    aapl_z = zscore(aapl_cascade, lookback=120)
    xlk_cascade = build(xlk_resid, orders=(1, 2, 3, 4), inner_window=10)
    xlk_z = zscore(xlk_cascade, lookback=120)
    spy_cascade = build(spy_resid, orders=(1, 2, 3, 4), inner_window=10)
    spy_z = zscore(spy_cascade, lookback=120)

    records = []
    t0 = time.time()
    for i, ev in enumerate(events):
        if (i + 1) % 30 == 0:
            print(f"  event {i+1}/{len(events)}  ({time.time()-t0:.1f}s)")
        d = pd.Timestamp(ev["date"])
        if d not in returns.index:
            continue

        end_loc = returns.index.get_loc(d)
        if end_loc < 30 or end_loc + 5 >= len(returns):
            continue

        # RAW event metrics
        raw_ret_event = float(returns["AAPL"].iloc[end_loc])
        raw_abs = abs(raw_ret_event)
        # GARCH-RESIDUAL event metrics
        if d not in aapl_resid.index:
            continue
        resid_loc = aapl_resid.index.get_loc(d)
        resid_event = float(aapl_resid.iloc[resid_loc])
        resid_abs = abs(resid_event)

        # Cascade slope at event (computed on RESIDUALS)
        slope_event = float(slope({k: aapl_z[k] for k in [1, 2, 3, 4]}).iloc[resid_loc]) \
            if resid_loc < len(aapl_z[1]) else np.nan
        if np.isnan(slope_event):
            continue

        records.append({
            "date": ev["date"],
            "label": ev["label"],
            "class": ev["class"],
            "asset": ev["asset"],
            "raw_ret_event": raw_ret_event,
            "raw_abs": raw_abs,
            "resid_event": resid_event,
            "resid_abs": resid_abs,
            "slope_event": slope_event,
        })

    df = pd.DataFrame(records)
    print(f"\nanalyzed {len(df)} events")

    # Correlations
    print("\n" + "=" * 78)
    print("CORRELATIONS")
    print("=" * 78)
    valid = df.dropna(subset=["slope_event", "raw_abs", "resid_abs"])
    n = len(valid)
    print(f"\n  n valid events: {n}")
    print(f"  Median |return| on event day: {valid['raw_abs'].median():.4f}")
    print(f"  Median |residual| on event day: {valid['resid_abs'].median():.4f}")
    print(f"  Median slope_event: {valid['slope_event'].median():+.4f}")

    # Spearman on raw
    r_raw, p_raw = sps.spearmanr(valid["slope_event"], valid["raw_abs"])
    # Spearman on GARCH-residual
    r_res, p_res = sps.spearmanr(valid["slope_event"], valid["resid_abs"])

    print(f"\n  Spearman(slope_event, |return|) on RAW returns: {r_raw:+.4f}  (p={p_raw:.2e})")
    print(f"  Spearman(slope_event, |residual|) on GARCH-residuals: {r_res:+.4f}  (p={p_res:.2e})")

    # Ratio: residual / raw
    if abs(r_raw) > 0.01:
        ratio = r_res / r_raw
        print(f"\n  Ratio (residual / raw): {ratio:+.3f}")
        if abs(ratio) > 0.5:
            print(f"  --> H3b effect is MORE THAN HALF independent of GARCH")
        elif abs(ratio) > 0.25:
            print(f"  --> H3b effect is partially GARCH-independent")
        else:
            print(f"  --> H3b effect is mostly GARCH-driven (like vol-peak)")

    # By event class
    print("\n  By event class (Spearman slope_event -> magnitude):")
    for cls in ["idiosyncratic", "systemic"]:
        sub = valid[valid["class"] == cls]
        if len(sub) < 5:
            continue
        r_raw_c, p_raw_c = sps.spearmanr(sub["slope_event"], sub["raw_abs"])
        r_res_c, p_res_c = sps.spearmanr(sub["slope_event"], sub["resid_abs"])
        print(f"    {cls} (n={len(sub)}):")
        print(f"      raw: {r_raw_c:+.4f}  (p={p_raw_c:.3f})")
        print(f"      garch-residual: {r_res_c:+.4f}  (p={p_res_c:.3f})")

    out_path = RESULTS_DIR / "h3b_garch_residual_test.json"
    with open(out_path, "w") as f:
        json.dump({
            "events": records,
            "summary": {
                "n_valid": n,
                "raw_spearman_r": float(r_raw),
                "raw_spearman_p": float(p_raw),
                "garch_residual_spearman_r": float(r_res),
                "garch_residual_spearman_p": float(p_res),
                "ratio": float(r_res / r_raw) if abs(r_raw) > 0.01 else None,
            },
        }, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
