# Inlined from the workbench version of referee_audit.py
import json
import os
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import ElasticNet, LinearRegression
import lightgbm as lgb
import catboost as cb
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


def har_rv(r, w_daily=1, w_weekly=5, w_monthly=22):
    rv = r ** 2
    return (rv.rolling(w_daily).mean() + rv.rolling(w_weekly).mean() + rv.rolling(w_monthly).mean()) / 3


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


def encompassing_by_horizon(r, train_end, test_start, test_end, new_var="z1"):
    cascade = compute_cascade(r)
    cs = compute_cascade_slope(cascade)
    z1 = cascade["V1"]
    har = har_rv(r)
    out = {}
    for h in [1, 2, 3, 5, 10, 20]:
        fwd = np.sqrt((r ** 2).rolling(h).sum().shift(-h))
        train = pd.DataFrame({"fwd": fwd, "har": har}).reindex(r[r.index <= train_end].index).dropna()
        test = pd.DataFrame({"fwd": fwd, "har": har, "z1": z1, "cs": cs}).reindex(
            r[(r.index >= test_start) & (r.index <= test_end)].index
        ).dropna()
        if len(train) < 100 or len(test) < 50:
            continue
        X_tr = sm.add_constant(train[["har"]], has_constant="add")
        X_te = sm.add_constant(test[["har"]], has_constant="add")
        mod_har = sm.OLS(train["fwd"], X_tr).fit()
        pred_har = mod_har.predict(X_te)
        new = test[new_var].values
        X = np.column_stack([pred_har.values, new])
        Xc = sm.add_constant(X, has_constant="add")
        m = sm.OLS(test["fwd"].values, Xc).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        out[h] = {
            "beta_new": float(m.params[2]),
            "t_new": float(m.tvalues[2]),
            "p_new": float(m.pvalues[2]),
            "n_test": int(len(test)),
        }
    return out


def rolling_z1_encompassing(r, ticker):
    fwd = np.sqrt((r ** 2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    cascade = compute_cascade(r)
    z1 = cascade["V1"]
    har = har_rv(r)
    end = pd.Timestamp("2024-12-31")
    cur = pd.Timestamp("2001-12-31")
    out = []
    while cur + pd.DateOffset(years=3) <= end:
        train_end = cur
        test_start = cur + pd.DateOffset(days=1)
        test_end = cur + pd.DateOffset(years=3)
        train = pd.DataFrame({"fwd": fwd, "har": har}).reindex(r[r.index <= train_end].index).dropna()
        test = pd.DataFrame({"fwd": fwd, "har": har, "z1": z1}).reindex(
            r[(r.index >= test_start) & (r.index <= test_end)].index
        ).dropna()
        if len(train) < 100 or len(test) < 100:
            cur = cur + pd.DateOffset(years=1)
            continue
        X_tr = sm.add_constant(train[["har"]], has_constant="add")
        X_te = sm.add_constant(test[["har"]], has_constant="add")
        mod_har = sm.OLS(train["fwd"], X_tr).fit()
        pred_har = mod_har.predict(X_te)
        X = np.column_stack([pred_har.values, test["z1"].values])
        Xc = sm.add_constant(X, has_constant="add")
        m = sm.OLS(test["fwd"].values, Xc).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        out.append({
            "ticker": ticker,
            "period": f"{test_start.year}-{test_end.year}",
            "beta_z1": float(m.params[2]),
            "p_z1": float(m.pvalues[2]),
        })
        cur = cur + pd.DateOffset(years=1)
    return out


def vif_diagnostics(r, train_end, test_start, test_end):
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    cascade = compute_cascade(r)
    cs = compute_cascade_slope(cascade)
    har = har_rv(r)
    var = r.rolling(22).var()
    df = pd.DataFrame({"har": har, "var": var,
                        "V1": cascade["V1"], "V2": cascade["V2"],
                        "V3": cascade["V3"], "V4": cascade["V4"],
                        "cs": cs}).reindex(r[(r.index >= test_start) & (r.index <= test_end)].index).dropna()
    if len(df) < 50:
        return None
    X = sm.add_constant(df[["har", "var", "V1", "V2", "V3", "V4", "cs"]], has_constant="add")
    vifs = {col: float(variance_inflation_factor(X.values, i + 1))
            for i, col in enumerate(["har", "var", "V1", "V2", "V3", "V4", "cs"])}
    return vifs


def nested_r2_oos(r, train_end, test_start, test_end):
    cascade = compute_cascade(r)
    cs = compute_cascade_slope(cascade)
    har = har_rv(r)
    var = r.rolling(22).var()
    fwd = np.sqrt((r ** 2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    train = pd.DataFrame({"fwd": fwd, "hv": r.rolling(22).var() * 252,
                          "har": har, "garch": var, "cs": cs}).reindex(
        r[r.index <= train_end].index
    ).dropna()
    test = pd.DataFrame({"fwd": fwd, "hv": r.rolling(22).var() * 252,
                         "har": har, "garch": var, "cs": cs}).reindex(
        r[(r.index >= test_start) & (r.index <= test_end)].index
    ).dropna()
    if len(train) < 100 or len(test) < 50:
        return None
    models = {
        "M1_hist": ["hv"],
        "M2_plus_HAR": ["hv", "har"],
        "M3_plus_GARCH": ["hv", "har", "garch"],
        "M4_plus_Cascade": ["hv", "har", "garch", "cs"],
    }
    oos_r2 = {}
    for name, cols in models.items():
        X_tr = sm.add_constant(train[cols], has_constant="add")
        X_te = sm.add_constant(test[cols], has_constant="add")
        mod = sm.OLS(train["fwd"], X_tr).fit()
        pred = mod.predict(X_te)
        sse = ((test["fwd"] - pred) ** 2).sum()
        sst = ((test["fwd"] - test["fwd"].mean()) ** 2).sum()
        oos_r2[name] = float(1 - sse / sst)
    return oos_r2


def ml_comparison(r, train_end, test_start, test_end):
    cascade = compute_cascade(r)
    cs = compute_cascade_slope(cascade)
    har = har_rv(r)
    fwd = np.sqrt((r ** 2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    df = pd.DataFrame({"fwd": fwd, "har": har, "cs": cs,
                        "V1": cascade["V1"], "V2": cascade["V2"],
                        "V3": cascade["V3"], "V4": cascade["V4"]}).dropna()
    train = df.reindex(r[r.index <= train_end].index).dropna()
    test = df.reindex(r[(r.index >= test_start) & (r.index <= test_end)].index).dropna()
    if len(train) < 100 or len(test) < 50:
        return None
    y_tr = train["fwd"].values
    y_te = test["fwd"].values
    out = {}
    feature_sets = {
        "HAR_only": ["har"],
        "HAR_plus_cascade": ["har", "cs"],
        "HAR_plus_all_levels": ["har", "V1", "V2", "V3", "V4", "cs"],
    }
    for name, feats in feature_sets.items():
        X_tr = train[feats].values
        X_te = test[feats].values
        lr = LinearRegression().fit(X_tr, y_tr)
        lr_mse = float(((y_te - lr.predict(X_te)) ** 2).mean())
        lgbm = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, max_depth=3,
                                    num_leaves=8, min_data_in_leaf=20, verbose=-1, random_state=42)
        lgbm.fit(X_tr, y_tr)
        lgbm_mse = float(((y_te - lgbm.predict(X_te)) ** 2).mean())
        cb_model = cb.CatBoostRegressor(iterations=100, learning_rate=0.05, depth=3,
                                          verbose=0, random_state=42)
        cb_model.fit(X_tr, y_tr)
        cb_mse = float(((y_te - cb_model.predict(X_te)) ** 2).mean())
        en = ElasticNet(alpha=0.01, l1_ratio=0.5, random_state=42, max_iter=2000)
        en.fit(X_tr, y_tr)
        en_mse = float(((y_te - en.predict(X_te)) ** 2).mean())
        out[name] = {
            "LinearReg_mse": lr_mse,
            "LightGBM_mse": lgbm_mse,
            "CatBoost_mse": cb_mse,
            "ElasticNet_mse": en_mse,
        }
    return out


def cer_with_costs(r, train_end, test_start, test_end, cost_bps_list):
    cascade = compute_cascade(r)
    cs = compute_cascade_slope(cascade)
    fwd = np.sqrt((r ** 2).rolling(FORWARD_DAYS).sum().shift(-FORWARD_DAYS))
    VOL_TARGET = 0.15
    TRADING_DAYS = 252
    train = pd.DataFrame({"fwd": fwd, "cs": cs}).reindex(r[r.index <= train_end].index).dropna()
    test = pd.DataFrame({"fwd": fwd, "cs": cs, "r": r}).reindex(
        r[(r.index >= test_start) & (r.index <= test_end)].index
    ).dropna()
    if len(train) < 100 or len(test) < 50:
        return None
    # Annualized forward vol (matches the original vol_timing_simple.py)
    fwd_vol_ann = pd.Series(np.nan, index=test.index)
    rets_arr = test["r"].values
    for i in range(len(test) - FORWARD_DAYS):
        fwd_vol_ann.iloc[i] = np.std(rets_arr[i + 1:i + 1 + FORWARD_DAYS]) * np.sqrt(TRADING_DAYS)
    test = test.assign(fwd_vol_ann=fwd_vol_ann)
    test = test.dropna(subset=["fwd_vol_ann"])
    # Fit signal: pred_vol = a + b * cs on train
    X_tr = sm.add_constant(train[["cs"]], has_constant="add")
    mod = sm.OLS(train["fwd"], X_tr).fit()
    test = test.copy()
    test["pred"] = mod.predict(sm.add_constant(test[["cs"]], has_constant="add"))
    test["pred"] = test["pred"].clip(0.05, 1.0)
    out = {}
    for cost_bps in cost_bps_list:
        pos = (VOL_TARGET / test["pred"]).clip(0.2, 2.0)
        gross_ret = pos * test["r"]
        turnover = pos.diff().abs().fillna(0)
        cost_ret = -turnover * (cost_bps / 10000)
        net_ret = gross_ret + cost_ret
        bh_ret = test["r"]
        cer_strat = float(net_ret.mean() - 0.5 * net_ret.var())
        cer_bh = float(bh_ret.mean() - 0.5 * bh_ret.var())
        sh_strat = float(net_ret.mean() / net_ret.std() * np.sqrt(252)) if net_ret.std() > 0 else 0
        sh_bh = float(bh_ret.mean() / bh_ret.std() * np.sqrt(252)) if bh_ret.std() > 0 else 0
        out[f"{cost_bps}_bps"] = {
            "CER_strat": cer_strat,
            "CER_bh": cer_bh,
            "CER_improvement": cer_strat - cer_bh,
            "Sharpe_strat": sh_strat,
            "Sharpe_bh": sh_bh,
            "Sharpe_improvement": sh_strat - sh_bh,
            "annualized_return": float(net_ret.mean() * 252),
            "annualized_vol": float(net_ret.std() * np.sqrt(252)),
            "total_turnover": float(turnover.sum()),
            "mean_position": float(pos.mean()),
        }
    return out


def main():
    us_returns, intl_returns = load_data()
    train_end = pd.Timestamp("2009-12-31")
    test_start = pd.Timestamp("2010-01-01")
    test_end = pd.Timestamp("2014-12-31")
    results = {}

    # 1. Encompassing by horizon (z1 and cs) on SPY H2
    print("=" * 70)
    print("1. ENCOMPASSING BY HORIZON (SPY H2 2010-2014)")
    print("=" * 70)
    r = us_returns["SPY"]
    z1_h = encompassing_by_horizon(r, train_end, test_start, test_end, new_var="z1")
    cs_h = encompassing_by_horizon(r, train_end, test_start, test_end, new_var="cs")
    print(f"{'h':<5} {'z1 beta':<12} {'z1 p':<10} {'cs beta':<12} {'cs p':<10}")
    for h in [1, 2, 3, 5, 10, 20]:
        z = z1_h.get(h, {})
        c = cs_h.get(h, {})
        z_sig = "***" if z.get("p_new", 1) < 0.001 else "**" if z.get("p_new", 1) < 0.01 else "*" if z.get("p_new", 1) < 0.05 else ""
        c_sig = "***" if c.get("p_new", 1) < 0.001 else "**" if c.get("p_new", 1) < 0.01 else "*" if c.get("p_new", 1) < 0.05 else ""
        print(f"{h:<5} {z.get('beta_new', 0):>+10.5f} {z_sig:<3} {z.get('p_new', 1):<8.3g} {c.get('beta_new', 0):>+10.5f} {c_sig:<3} {c.get('p_new', 1):<8.3g}")
    results["encompassing_by_horizon"] = {"z1": z1_h, "cs": cs_h}

    # 2. Rolling z1 encompassing
    print()
    print("=" * 70)
    print("2. ROLLING z1 ENCOMPASSING (184 windows, 10 assets)")
    print("=" * 70)
    print(f"{'Asset':<6} {'Windows':<10} {'Sig':<6} {'Positive':<10} {'Sig frac':<10}")
    rolling = {}
    for ticker in US_TICKERS + INTL_TICKERS:
        src = us_returns if ticker in us_returns.columns else intl_returns
        rows = rolling_z1_encompassing(src[ticker], ticker)
        sig = sum(r["p_z1"] < 0.05 for r in rows)
        pos = sum(r["beta_z1"] > 0 for r in rows)
        rolling[ticker] = {"windows": len(rows), "sig": sig, "pos": pos,
                            "sig_frac": sig / len(rows) if rows else 0}
        print(f"{ticker:<6} {len(rows):<10} {sig:<6} {pos:<10} {sig/len(rows) if rows else 0:.1%}")
    total_w = sum(r["windows"] for r in rolling.values())
    total_sig = sum(r["sig"] for r in rolling.values())
    total_pos = sum(r["pos"] for r in rolling.values())
    print(f"OVERALL: {total_sig}/{total_w} sig ({total_sig/total_w:.1%}), {total_pos}/{total_w} positive ({total_pos/total_w:.1%})")
    results["rolling_z1_encompassing"] = {"per_asset": rolling, "overall": {
        "total_windows": total_w, "sig": total_sig, "pos": total_pos,
        "sig_frac": total_sig / total_w, "pos_frac": total_pos / total_w,
    }}

    # 3. VIF
    print()
    print("=" * 70)
    print("3. VIF DIAGNOSTICS (SPY H2 2010-2014)")
    print("=" * 70)
    vifs = vif_diagnostics(r, train_end, test_start, test_end)
    if vifs:
        for col, vif in vifs.items():
            flag = " <-- HIGH (VIF>10)" if vif > 10 else ""
            print(f"  {col:<6}: {vif:.2f}{flag}")
    results["vif_diagnostics"] = vifs

    # 4. OOS nested R^2
    print()
    print("=" * 70)
    print("4. OUT-OF-SAMPLE NESTED R^2 (SPY H2 2010-2014)")
    print("=" * 70)
    oos_r2 = nested_r2_oos(r, train_end, test_start, test_end)
    if oos_r2:
        for k, v in oos_r2.items():
            print(f"  {k:<20}: OOS R^2 = {v:.4f}")
        m1 = oos_r2["M1_hist"]
        m2 = oos_r2["M2_plus_HAR"]
        m3 = oos_r2["M3_plus_GARCH"]
        m4 = oos_r2["M4_plus_Cascade"]
        print(f"  Delta R^2 (HAR over Hist):     {m2 - m1:+.4f}")
        print(f"  Delta R^2 (GARCH over HAR):   {m3 - m2:+.4f}")
        print(f"  Delta R^2 (Cascade over GARCH): {m4 - m3:+.4f}")
    results["oos_nested_r2"] = oos_r2

    # 5. ML comparison
    print()
    print("=" * 70)
    print("5. ML COMPARISON (SPY H2 2010-2014, MSE on test set)")
    print("=" * 70)
    ml = ml_comparison(r, train_end, test_start, test_end)
    if ml:
        for fs, models in ml.items():
            print(f"\\n  Feature set: {fs}")
            for mname, mse in models.items():
                print(f"    {mname:<15}: MSE = {mse:.6f}")
    results["ml_comparison"] = ml

    # 6. CER with transaction costs
    print()
    print("=" * 70)
    print("6. CER WITH TRANSACTION COSTS (SPY H2 2010-2014, vol-timing)")
    print("=" * 70)
    cer = cer_with_costs(r, train_end, test_start, test_end, [0, 5, 10, 20])
    if cer:
        for cost, vals in cer.items():
            print(f"\\n  {cost}:")
            for k, v in vals.items():
                print(f"    {k:<22}: {v:+.5f}")
    results["cer_with_costs"] = cer

    os.makedirs("results", exist_ok=True)
    with open("results/referee_audit.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print()
    print("Saved results/referee_audit.json")


if __name__ == "__main__":
    main()
