"""GARCH-residual test for the H3b PANEL result (3 representative stocks)."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore
from volcascade.io import load_prices

TICKERS = ["AAPL", "MSFT", "JPM"]
prices = load_prices(TICKERS, start="2015-01-01", end="2024-12-31")
returns = np.log(prices / prices.shift(1)).dropna()

results = []
for asset in TICKERS:
    rets = returns[asset].dropna()
    am = arch_model(rets * 100, mean="Constant", vol="GARCH", p=1, q=1,
                    dist="t", rescale=False)
    res = am.fit(disp="off", show_warning=False, options={"maxiter": 50})
    g_res = res.std_resid.dropna()

    cascade_raw = build(rets, orders=(1, 2, 3, 4), inner_window=10)
    z_raw = zscore(cascade_raw, lookback=120)
    s_raw = slope({k: z_raw[k] if not isinstance(z_raw[k], pd.DataFrame) else z_raw[k][asset]
                   for k in [1, 2, 3, 4]})

    cascade_res = build(g_res, orders=(1, 2, 3, 4), inner_window=10)
    z_res = zscore(cascade_res, lookback=120)
    s_res = slope(dict(z_res))

    rets_q = rets.copy()
    rets_q.index = pd.to_datetime(rets_q.index)
    quarters = rets_q.index.to_period("Q")
    raw_records, res_records = [], []
    for q in quarters.unique():
        mask = quarters == q
        q_rets = rets_q[mask]
        if len(q_rets) < 5:
            continue
        top_idx = q_rets.abs().idxmax()
        loc = rets.index.get_loc(top_idx)
        abs_ret = abs(float(rets.iloc[loc]))
        if not pd.isna(s_raw.iloc[loc]):
            raw_records.append({"slope": float(s_raw.iloc[loc]), "abs": abs_ret})
        if not pd.isna(s_res.iloc[loc]):
            res_records.append({"slope": float(s_res.iloc[loc]), "abs": abs_ret})
    r_raw, _ = sps.spearmanr([d["slope"] for d in raw_records], [d["abs"] for d in raw_records]) if len(raw_records) >= 10 else (np.nan, np.nan)
    r_res, _ = sps.spearmanr([d["slope"] for d in res_records], [d["abs"] for d in res_records]) if len(res_records) >= 10 else (np.nan, np.nan)
    ratio = r_res / r_raw if abs(r_raw) > 0.01 else None
    results.append({"asset": asset, "raw_r": float(r_raw), "res_r": float(r_res),
                    "ratio": float(ratio) if ratio is not None else None,
                    "raw_n": len(raw_records), "res_n": len(res_records)})
    print(f" {asset}: raw r={r_raw:+.4f} (n={len(raw_records)}) res r={r_res:+.4f} ratio={ratio:+.3f}" if ratio is not None else f" {asset}: ratio=n/a")

med_raw = float(np.median([r["raw_r"] for r in results]))
med_res = float(np.median([r["res_r"] for r in results]))
print(f"\n median raw: {med_raw:+.4f}, median residual: {med_res:+.4f}, ratio: {med_res/med_raw:+.3f}")

out = {"results": results, "median_raw": med_raw, "median_residual": med_res,
       "ratio": med_res/med_raw if abs(med_raw) > 0.01 else None}
with open(ROOT / "results" / "h3b_panel_garch_residual.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\nsaved to {ROOT/'results'/'h3b_panel_garch_residual.json'}")
