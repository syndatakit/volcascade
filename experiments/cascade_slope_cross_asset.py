"""Cascade-slope cross-asset audit. See CASCADE_SLOPE_README.md for details."""
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
def compute_cascade_slope(cascade):
    K = cascade.shape[1]
    k = np.arange(1, K + 1).astype(float)
    k_centered = k - k.mean()
    denom = (k_centered ** 2).sum()
    out = []
    for t in cascade.index:
        z = cascade.loc[t].values
        if np.any(np.isnan(z)):
            out.append(np.nan)
            continue
        out.append((k_centered * (z - z.mean())).sum() / denom)
    return pd.Series(out, index=cascade.index)
def forward_rv(r, h=FORWARD_DAYS):
    return np.sqrt((r ** 2).rolling(h).sum().shift(-h))
def har_predict(r, train_end, test_start, test_end):
    rv = r ** 2
    har_full = (rv + rv.rolling(5).mean() + rv.rolling(22).mean()) / 3
    test_idx = r[(r.index >= test_start) & (r.index <= test_end)].index
    train = pd.DataFrame({"fwd": forward_rv(r), "har": har_full}).reindex(r[r.index <= train_end].index).dropna()
    test = pd.DataFrame({"fwd": forward_rv(r), "har": har_full}).reindex(test_idx).dropna()
    X_tr = sm.add_constant(train[["har"]], has_constant="add")
    X_te = sm.add_constant(test[["har"]], has_constant="add")
    mod = sm.OLS(train["fwd"], X_tr).fit()
    return mod.predict(X_te).values, test.index
def encompassing_with_cs(r, train_end, test_start, test_end):
    fwd = forward_rv(r)
    cascade = compute_cascade(r)
    cs = compute_cascade_slope(cascade)
    har_p, test_idx = har_predict(r, train_end, test_start, test_end)
    fwd_te = fwd.reindex(test_idx).dropna()
    cs_te = cs.reindex(test_idx).fillna(0)
    common = fwd_te.index.intersection(cs_te.index)
    n = len(common)
    if n < 50:
        return None
    X = np.column_stack([har_p[:n], cs_te.reindex(common).values])
    Xc = sm.add_constant(X, has_constant="add")
    mod = sm.OLS(fwd_te.reindex(common).values, Xc).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return {"beta_cs": float(mod.params[2]), "se_cs": float(mod.bse[2]), "t_cs": float(mod.tvalues[2]), "p_cs": float(mod.pvalues[2]), "r2": float(mod.rsquared), "n_test": int(n)}
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
def run_pooled(panel):
    asset_d = pd.get_dummies(panel["asset"], prefix="a", drop_first=True).astype(float)
    X = pd.concat([pd.Series(panel["har"].values, index=panel.index, name="har"), pd.Series(panel["cs"].values, index=panel.index, name="cs"), asset_d.reset_index(drop=True).set_index(panel.index)], axis=1)
    X = sm.add_constant(X, has_constant="add")
    mod = sm.OLS(panel["rv"].values, X).fit(cov_type="cluster", cov_kwds={"groups": panel["asset"].values})
    out = {"n_obs": int(len(panel)), "n_assets": int(panel["asset"].nunique()), "n_dates": int(panel["date"].nunique()), "har_coef": float(mod.params["har"]), "har_t": float(mod.tvalues["har"]), "har_p": float(mod.pvalues["har"]), "cs_coef": float(mod.params["cs"]), "cs_t": float(mod.tvalues["cs"]), "cs_p": float(mod.pvalues["cs"]), "r2": float(mod.rsquared), "model": "asset_FE_cluster_by_asset"}
    panel = panel.copy()
    for col in ["rv", "har", "cs"]:
        panel[f"{col}_2way"] = panel[col] - panel.groupby("date")[col].transform("mean") - panel.groupby("asset")[col].transform("mean") + panel[col].mean()
    X2 = pd.DataFrame({"const": 1.0, "har": panel["har_2way"], "cs": panel["cs_2way"]}, index=panel.index)
    mod2 = sm.OLS(panel["rv_2way"].values, X2).fit(cov_type="cluster", cov_kwds={"groups": panel["asset"].values})
    out["two_way"] = {"har_coef": float(mod2.params["har"]), "har_t": float(mod2.tvalues["har"]), "har_p": float(mod2.pvalues["har"]), "cs_coef": float(mod2.params["cs"]), "cs_t": float(mod2.tvalues["cs"]), "cs_p": float(mod2.pvalues["cs"]), "r2_within": float(mod2.rsquared), "model": "date_plus_asset_FE_cluster_by_asset"}
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
        cs = compute_cascade_slope(cascade)
        har_p, har_idx = har_predict(r, train_end, test_start, test_end)
        for i, d in enumerate(har_idx):
            f = fwd.reindex([d]).dropna()
            if len(f) == 0:
                continue
            rows.append({"date": d, "asset": ticker, "rv": float(f.iloc[0]), "har": float(har_p[i]), "cs": float(cs.reindex([d]).fillna(0).iloc[0])})
    return pd.DataFrame(rows).dropna()
def run_rolling(r, ticker):
    fwd = forward_rv(r)
    cascade = compute_cascade(r)
    cs = compute_cascade_slope(cascade)
    har_full = (r ** 2 + (r ** 2).rolling(5).mean() + (r ** 2).rolling(22).mean()) / 3
    end = pd.Timestamp("2024-12-31")
    cur = pd.Timestamp("2001-12-31")
    out = []
    while cur + pd.DateOffset(years=3) <= end:
        train_end = cur
        test_start = cur + pd.DateOffset(days=1)
        test_end = cur + pd.DateOffset(years=3)
        train = pd.DataFrame({"fwd": fwd, "har": har_full, "cs": cs}).reindex(r[r.index <= train_end].index).dropna()
        test = pd.DataFrame({"fwd": fwd, "har": har_full, "cs": cs}).reindex(r[(r.index >= test_start) & (r.index <= test_end)].index).dropna()
        if len(train) < 100 or len(test) < 100:
            cur = cur + pd.DateOffset(years=1)
            continue
        X_tr = sm.add_constant(train[["har"]], has_constant="add")
        X_te = sm.add_constant(test[["har"]], has_constant="add")
        mod_har = sm.OLS(train["fwd"], X_tr).fit()
        pred = mod_har.predict(X_te)
        X = np.column_stack([pred.values, test["cs"].values])
        Xc = sm.add_constant(X, has_constant="add")
        m = sm.OLS(test["fwd"].values, Xc).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        out.append({"ticker": ticker, "period": f"{test_start.year}-{test_end.year}", "beta_cs": float(m.params[2]), "p_cs": float(m.pvalues[2])})
        cur = cur + pd.DateOffset(years=1)
    return out
def main():
    us_returns, intl_returns = load_data()
    h2_results = {}
    for ticker in US_TICKERS:
        h2_results[ticker] = encompassing_with_cs(us_returns[ticker], pd.Timestamp("2009-12-31"), pd.Timestamp("2010-01-01"), pd.Timestamp("2014-12-31"))
    h3_results = {}
    for ticker in US_TICKERS + INTL_TICKERS:
        src = us_returns if ticker in us_returns.columns else intl_returns
        h3_results[ticker] = encompassing_with_cs(src[ticker], pd.Timestamp("2019-12-31"), pd.Timestamp("2020-01-01"), pd.Timestamp("2024-12-31"))
    panel = build_h3_panel(us_returns, intl_returns)
    pooled = run_pooled(panel)
    rolling = {}
    for ticker in US_TICKERS + INTL_TICKERS:
        src = us_returns if ticker in us_returns.columns else intl_returns
        rows = run_rolling(src[ticker], ticker)
        sig = sum(r["p_cs"] < 0.05 for r in rows)
        neg = sum(r["beta_cs"] < 0 for r in rows)
        rolling[ticker] = {"windows": len(rows), "significant_5pct": sig, "negative_beta": neg, "sig_frac": sig / len(rows) if rows else 0, "rows": rows}
    total_w = sum(r["windows"] for r in rolling.values())
    total_sig = sum(r["significant_5pct"] for r in rolling.values())
    total_neg = sum(r["negative_beta"] for r in rolling.values())
    overall = {"total_windows": total_w, "significant_5pct": total_sig, "negative_beta": total_neg, "sig_frac": total_sig / total_w if total_w else 0, "neg_frac": total_neg / total_w if total_w else 0}
    os.makedirs("results", exist_ok=True)
    with open("results/cascade_slope_per_asset.json", "w") as f:
        json.dump({"h2_2010_2014_us": h2_results, "h3_2020_2024_all": h3_results}, f, indent=2)
    with open("results/cascade_slope_pooled.json", "w") as f:
        json.dump(pooled, f, indent=2)
    with open("results/cascade_slope_rolling.json", "w") as f:
        json.dump({"per_asset": rolling, "overall": overall}, f, indent=2)
if __name__ == "__main__":
    main()
