"""Cross-asset forecast-encompassing audit.

Tests whether the cascade's level-1 statistic (z-scored V1, z-scored realized
volatility) adds information beyond the HAR baseline in a forecast-encompassing
regression. Run on H2 (US 5 assets, 2010-2014) and H3 (all 10 US+intl assets,
2020-2024). Also reports a pooled panel regression with asset + date fixed
effects and asset-clustered standard errors.

The new variable here is z-scored V1 (z1), the first level of the cascade.
This is conceptually distinct from the cascade slope beta_t, which is the
within-timepoint OLS slope of (1, 2, 3, 4) on (z^1, z^2, z^3, z^4). Both are
part of the cascade representation; they test different hypotheses.

Note: this script does NOT include a DM test. The DM test on (HAR vs HAR+z1)
shows that z1 does not significantly improve out-of-sample MSE on 5-year
windows for any of the 10 assets (consistent with the broader vol-forecasting
literature where RV persistence makes MSE improvements hard to obtain).

Run: python experiments/cross_asset_audit.py
Outputs: results/cross_asset_encompassing.json, results/cross_asset_panel.json
"""

from __future__ import annotations

import json
import os
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf

warnings.filterwarnings("ignore")
np.random.seed(42)


INNER_W = 10
ZSCORE_LOOKBACK = 120
FORWARD_DAYS = 5

US_TICKERS = ["SPY", "XLK", "XLF", "XLV", "XLE"]
INTL_TICKERS = ["EWJ", "EFA", "GLD", "TSM", "ASHR"]


def realized_vol(r, w=INNER_W):
    return np.sqrt((r ** 2).rolling(w).sum())


def rolling_std(s, w=INNER_W):
    return s.rolling(w).std()


def zscore(s, lookback=ZSCORE_LOOKBACK):
    return (s - s.rolling(lookback).mean()) / s.rolling(lookback).std()


def compute_cascade(r, K=4):
    V1 = realized_vol(r, INNER_W)
    levels = [V1]
    for k in range(2, K + 1):
        levels.append(rolling_std(levels[-1], INNER_W))
    levels = [zscore(v, ZSCORE_LOOKBACK) for v in levels]
    return pd.concat(levels, axis=1, keys=[f"V{k+1}" for k in range(K)])


def forward_rv(r, h=FORWARD_DAYS):
    return np.sqrt((r ** 2).rolling(h).sum().shift(-h))


def har_predict(r, train_end, test_start, test_end):
    """Constant HAR baseline trained on the pre-train-end window."""
    rv = r ** 2
    har_full = (rv + rv.rolling(5).mean() + rv.rolling(22).mean()) / 3
    test_idx = r[(r.index >= test_start) & (r.index <= test_end)].index
    last_train_har = har_full[har_full.index <= train_end].dropna()
    last_har_value = float(last_train_har.iloc[-1]) if len(last_train_har) > 0 else 0.0
    return np.full(len(test_idx), last_har_value), test_idx


def forecast_encompassing(targets, base_pred, new_pred, maxlags=5):
    X = np.column_stack([base_pred, new_pred])
    Xc = sm.add_constant(X, has_constant="add")
    model = sm.OLS(targets, Xc).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    return {
        "beta_new": float(model.params[2]),
        "se_new": float(model.bse[2]),
        "t_new": float(model.tvalues[2]),
        "p_new": float(model.pvalues[2]),
        "r2": float(model.rsquared),
    }


def load_data(data_dir="data", refresh=False):
    us_path = os.path.join(data_dir, "returns_us.csv")
    intl_path = os.path.join(data_dir, "returns_intl.csv")
    if refresh or not (os.path.exists(us_path) and os.path.exists(intl_path)):
        os.makedirs(data_dir, exist_ok=True)
        us = yf.download(US_TICKERS, start="2000-01-01", end="2026-07-01", progress=False, auto_adjust=True)["Close"]
        intl = yf.download(INTL_TICKERS, start="2004-01-01", end="2026-07-01", progress=False, auto_adjust=True)["Close"]
        us_returns = np.log(us / us.shift(1)).dropna(how="all")
        intl_returns = np.log(intl / intl.shift(1)).dropna(how="all")
        us_returns.to_csv(us_path)
        intl_returns.to_csv(intl_path)
    return pd.read_csv(us_path, index_col=0, parse_dates=True), pd.read_csv(intl_path, index_col=0, parse_dates=True)


def run_encompassing(r, train_end, test_start, test_end):
    fwd = forward_rv(r)
    cascade = compute_cascade(r)
    har_p, har_idx = har_predict(r, train_end, test_start, test_end)
    targets = fwd.reindex(har_idx).dropna().values
    n_min = len(targets)
    z1 = cascade["V1"].reindex(har_idx).fillna(0).values[:n_min]
    har_p_a = har_p[:n_min]
    res = forecast_encompassing(targets, har_p_a, z1)
    res["n_test"] = int(n_min)
    res["train_end"] = str(train_end.date())
    res["test_window"] = f"{test_start.date()}_{test_end.date()}"
    return res


def run_panel(panel):
    asset_d = pd.get_dummies(panel["asset"], prefix="a", drop_first=True).astype(float)
    X = pd.concat(
        [
            pd.Series(panel["har"].values, index=panel.index, name="har"),
            pd.Series(panel["z1"].values, index=panel.index, name="z1"),
            asset_d.reset_index(drop=True).set_index(panel.index),
        ],
        axis=1,
    )
    X = sm.add_constant(X, has_constant="add")
    y = panel["rv"].values
    mod = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": panel["asset"].values})
    out = {
        "n_obs": int(len(panel)),
        "n_assets": int(panel["asset"].nunique()),
        "n_dates": int(panel["date"].nunique()),
        "har_coef": float(mod.params["har"]),
        "har_t": float(mod.tvalues["har"]),
        "har_p": float(mod.pvalues["har"]),
        "z1_coef": float(mod.params["z1"]),
        "z1_t": float(mod.tvalues["z1"]),
        "z1_p": float(mod.pvalues["z1"]),
        "r2": float(mod.rsquared),
        "model": "asset_FE_cluster_by_asset",
    }
    panel = panel.copy()
    for col in ["rv", "har", "z1"]:
        panel[f"{col}_2way"] = (
            panel[col]
            - panel.groupby("date")[col].transform("mean")
            - panel.groupby("asset")[col].transform("mean")
            + panel[col].mean()
        )
    X2 = pd.DataFrame({"const": 1.0, "har": panel["har_2way"], "z1": panel["z1_2way"]}, index=panel.index)
    y2 = panel["rv_2way"]
    mod2 = sm.OLS(y2, X2).fit(cov_type="cluster", cov_kwds={"groups": panel["asset"].values})
    out["two_way"] = {
        "har_coef": float(mod2.params["har"]),
        "har_t": float(mod2.tvalues["har"]),
        "har_p": float(mod2.pvalues["har"]),
        "z1_coef": float(mod2.params["z1"]),
        "z1_t": float(mod2.tvalues["z1"]),
        "z1_p": float(mod2.pvalues["z1"]),
        "r2_within": float(mod2.rsquared),
        "model": "date_plus_asset_FE_cluster_by_asset",
    }
    return out


def build_h3_panel(us_returns, intl_returns):
    train_end = pd.Timestamp("2019-12-31")
    test_start = pd.Timestamp("2020-01-01")
    test_end = pd.Timestamp("2024-12-31")
    rows = []
    for ticker in list(us_returns.columns) + list(intl_returns.columns):
        src = us_returns if ticker in us_returns.columns else intl_returns
        r = src[ticker]
        fwd = forward_rv(r)
        cascade = compute_cascade(r)
        har_p, har_idx = har_predict(r, train_end, test_start, test_end)
        for i, d in enumerate(har_idx):
            f = fwd.reindex([d]).dropna()
            if len(f) == 0:
                continue
            rows.append({
                "date": d,
                "asset": ticker,
                "rv": float(f.iloc[0]),
                "har": float(har_p[i]),
                "z1": float(cascade["V1"].reindex([d]).fillna(0).iloc[0]),
            })
    return pd.DataFrame(rows).dropna()


def main():
    us_returns, intl_returns = load_data()

    h2_results = {}
    train_end = pd.Timestamp("2009-12-31")
    test_start = pd.Timestamp("2010-01-01")
    test_end = pd.Timestamp("2014-12-31")
    for ticker in US_TICKERS:
        h2_results[ticker] = run_encompassing(us_returns[ticker], train_end, test_start, test_end)

    h3_results = {}
    train_end = pd.Timestamp("2019-12-31")
    test_start = pd.Timestamp("2020-01-01")
    test_end = pd.Timestamp("2024-12-31")
    for ticker in US_TICKERS + INTL_TICKERS:
        src = us_returns if ticker in us_returns.columns else intl_returns
        h3_results[ticker] = run_encompassing(src[ticker], train_end, test_start, test_end)

    panel = build_h3_panel(us_returns, intl_returns)
    panel_results = run_panel(panel)

    os.makedirs("results", exist_ok=True)
    with open("results/cross_asset_encompassing.json", "w") as f:
        json.dump({
            "h2_2010_2014_us": h2_results,
            "h3_2020_2024_all": h3_results,
            "summary": {
                "h2_significant_5pct": sum(v["p_new"] < 0.05 for v in h2_results.values()),
                "h2_positive_beta": sum(v["beta_new"] > 0 for v in h2_results.values()),
                "h2_n": len(h2_results),
                "h3_significant_5pct": sum(v["p_new"] < 0.05 for v in h3_results.values()),
                "h3_positive_beta": sum(v["beta_new"] > 0 for v in h3_results.values()),
                "h3_n": len(h3_results),
            },
        }, f, indent=2)
    with open("results/cross_asset_panel.json", "w") as f:
        json.dump(panel_results, f, indent=2)


if __name__ == "__main__":
    main()
