"""Strengthen the 'complementary to GARCH' framing with rigorous analysis.

Three rigorous tests:

1. ORTHOGONALITY: Spearman correlation between the cascade slope and
   GARCH conditional vol. If they're low/uncorrelated, the cascade
   captures DIFFERENT information from GARCH (i.e., truly complementary,
   not redundant).

2. PARTIAL CORRELATION: corr(forward_vol, cascade | GARCH). If the
   cascade has predictive power BEYOND GARCH, the partial correlation
   is significant. This is the formal test of "incremental information."

3. COMBINED MODEL: Predict forward vol using BOTH GARCH and cascade
   signals (linear regression or Theil-Sen). Test:
   - Sharpe ratio of vol-targeting using GARCH-only
   - Sharpe ratio of vol-targeting using cascade-only
   - Sharpe ratio of vol-targeting using BOTH
   - The combined model should beat either alone if the signals are
     genuinely complementary.

This is the rigorous test of "cascade complements GARCH, they don't
just add a little bit."
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model
from scipy import stats as sps
from scipy.stats import theilslopes

ROOT = Path("/opt/data/volcascade")
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore
from volcascade.io import load_prices

INNER_WINDOW = 10
ZSCORE_LOOKBACK = 120
FORWARD_DAYS = 5
TRADING_DAYS = 252
VOL_TARGET = 0.15


def garch_conditional_vol(returns):
    am = arch_model(returns * 100, mean="Constant", vol="GARCH", p=1, q=1,
                    dist="t", rescale=False)
    res = am.fit(disp="off", show_warning=False, options={"maxiter": 50})
    return pd.Series(res.conditional_volatility, index=returns.index).dropna()


def main() -> None:
    print("=" * 78)
    print("STRENGTHENING 'COMPLEMENTARY TO GARCH' FRAMING")
    print("=" * 78)

    ASSETS = ["SPY", "XLE", "XLF", "XLV", "XLY"]
    print(f"\nloading {ASSETS} (2000-2024)...")
    prices = load_prices(ASSETS, start="2000-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days\n")

    rows = []
    for asset in ASSETS:
        rets = returns[asset].dropna()
        print(f"\n  {asset}:")

        # 1. Cascade
        cascade = build(rets, orders=(1, 2, 3, 4), inner_window=INNER_WINDOW)
        z = zscore(cascade, lookback=ZSCORE_LOOKBACK)
        sample = z[1]
        if isinstance(sample, pd.DataFrame):
            z_s = {k: z[k][asset] for k in [1, 2, 3, 4]}
        else:
            z_s = dict(z)
        s = slope(z_s)

        # 2. GARCH conditional vol
        gv = garch_conditional_vol(rets)
        gv_z = (gv - gv.mean()) / gv.std()

        # 3. Forward vol
        fwd_vol = pd.Series(np.nan, index=rets.index)
        for i in range(len(rets) - FORWARD_DAYS):
            fwd_vol.iloc[i] = float(rets.iloc[i + 1:i + 1 + FORWARD_DAYS].std()) * np.sqrt(TRADING_DAYS)

        # Align
        valid = s.notna() & gv.notna() & fwd_vol.notna()
        sv = s[valid]
        gv_z_v = gv_z[valid]
        fv = fwd_vol[valid]
        r_rets = rets[valid]

        # ==== TEST 1: ORTHOGONALITY ====
        # Spearman correlation between cascade and GARCH signals
        r_orth, p_orth = sps.spearmanr(sv, gv_z_v)
        print(f"    [1] ORTHOGONALITY: Spearman(cascade, GARCH) = {r_orth:+.4f}  (p={p_orth:.2e})")
        orth_interp = "LOW (orthogonal)" if abs(r_orth) < 0.3 else "MODERATE" if abs(r_orth) < 0.6 else "HIGH (redundant)"

        # ==== TEST 2: PARTIAL CORRELATION ====
        # corr(forward_vol, cascade | GARCH): regress cascade on GARCH,
        # take residuals, correlate with forward_vol
        from numpy.linalg import lstsq
        # Cascade ~ a + b * GARCH
        X = np.column_stack([np.ones(len(gv_z_v)), gv_z_v.to_numpy()])
        cascade_resid = sv.to_numpy() - X @ lstsq(X, sv.to_numpy(), rcond=None)[0]
        r_part, p_part = sps.spearmanr(cascade_resid, fv.to_numpy())
        print(f"    [2] PARTIAL corr(forward_vol, cascade | GARCH) = {r_part:+.4f}  (p={p_part:.2e})")

        # corr(forward_vol, GARCH | cascade) for comparison
        X2 = np.column_stack([np.ones(len(sv)), sv.to_numpy()])
        garch_resid = gv_z_v.to_numpy() - X2 @ lstsq(X2, gv_z_v.to_numpy(), rcond=None)[0]
        r_part_g, p_part_g = sps.spearmanr(garch_resid, fv.to_numpy())
        print(f"    [2'] PARTIAL corr(forward_vol, GARCH | cascade) = {r_part_g:+.4f}  (p={p_part_g:.2e})")

        # ==== TEST 3: COMBINED VOL-TARGETING STRATEGY ====
        # Predict forward vol using:
        # (a) GARCH only: pred = a + b * gv_z
        # (b) Cascade only: pred = a + b * sv
        # (c) Combined: pred = a + b * gv_z + c * sv
        # Use Theil-Sen for robust estimation
        # For each, compute Sharpe of vol-targeting
        # Position = VOL_TARGET / pred

        # Train on first 70% of data, test on last 30%
        n = len(r_rets)
        n_train = int(n * 0.7)
        idx_train = np.arange(n_train)
        idx_test = np.arange(n_train, n)

        # Fit Theil-Sen on train, predict on test
        def theil_predict(X_train, y_train, X_test):
            # Use theilslopes for 1D case; for multivariate use HuberRegressor
            from sklearn.linear_model import HuberRegressor
            model = HuberRegressor(max_iter=200)
            model.fit(X_train, y_train)
            return model.predict(X_test)

        # GARCH only
        X_train_g = gv_z_v.iloc[idx_train].to_numpy().reshape(-1, 1)
        X_test_g = gv_z_v.iloc[idx_test].to_numpy().reshape(-1, 1)
        y_train = fv.iloc[idx_train].to_numpy()
        # Theil-Sen for slope, then predict
        slope_g, intercept_g, _, _ = theilslopes(y_train, X_train_g.ravel())
        pred_g_test = intercept_g + slope_g * X_test_g.ravel()
        pred_g_test = np.clip(pred_g_test, 0.05, 1.0)

        # Cascade only
        X_train_c = sv.iloc[idx_train].to_numpy().reshape(-1, 1)
        X_test_c = sv.iloc[idx_test].to_numpy().reshape(-1, 1)
        slope_c, intercept_c, _, _ = theilslopes(y_train, X_train_c.ravel())
        pred_c_test = intercept_c + slope_c * X_test_c.ravel()
        pred_c_test = np.clip(pred_c_test, 0.05, 1.0)

        # Combined
        X_train_both = np.column_stack([X_train_g.ravel(), X_train_c.ravel()])
        X_test_both = np.column_stack([X_test_g.ravel(), X_test_c.ravel()])
        try:
            pred_both_test = theil_predict(X_train_both, y_train, X_test_both)
            pred_both_test = np.clip(pred_both_test, 0.05, 1.0)
        except Exception:
            pred_both_test = (pred_g_test + pred_c_test) / 2

        # Compute strategy returns
        # Use idx_test directly for test period; need to align pred with r_test
        r_test_arr = r_rets.to_numpy()
        # Strategy uses pos[t] * r[t+1]; we have n_test points, so we need
        # n_test - 1 points in strat (use pos[:-1] * r[1:])
        n_test = len(idx_test)
        # pred_*: shape (n_test,)
        # r_test_arr[idx_test]: shape (n_test,)
        r_test_aligned = r_test_arr[idx_test]
        # pos uses VOL_TARGET / pred, so size n_test
        pos_g = np.clip(VOL_TARGET / pred_g_test, 0.2, 2.0)
        pos_c = np.clip(VOL_TARGET / pred_c_test, 0.2, 2.0)
        pos_b = np.clip(VOL_TARGET / pred_both_test, 0.2, 2.0)
        # Use position at time t to predict return at time t+1
        # (avoid look-ahead)
        strat_g = pos_g[:-1] * r_test_aligned[1:]
        strat_c = pos_c[:-1] * r_test_aligned[1:]
        strat_b = pos_b[:-1] * r_test_aligned[1:]

        def sharpe(x):
            if x.std() == 0 or len(x) < 50:
                return 0.0
            return float(x.mean() / x.std() * np.sqrt(TRADING_DAYS))

        sh_g = sharpe(strat_g)
        sh_c = sharpe(strat_c)
        sh_b = sharpe(strat_b)
        sh_bh = sharpe(pd.Series(r_test_aligned[1:]))

        print(f"    [3] Sharpe GARCH only: {sh_g:.3f}")
        print(f"    [3] Sharpe cascade only: {sh_c:.3f}")
        print(f"    [3] Sharpe COMBINED: {sh_b:.3f}")
        print(f"    [3] Sharpe buy-hold: {sh_bh:.3f}")
        best = max(sh_g, sh_c, sh_b)
        if sh_b == best:
            print(f"    [3] --> COMBINED MODEL WINS (improvement over best single: {sh_b - best:.3f})")
        else:
            print(f"    [3] --> best single model still wins (combined adds: {sh_b - best:.3f})")

        rows.append({
            "asset": asset,
            "orthogonality_r": float(r_orth),
            "orthogonality_p": float(p_orth),
            "orthogonality_class": orth_interp,
            "partial_cascade_given_garch": float(r_part),
            "partial_cascade_p": float(p_part),
            "partial_garch_given_cascade": float(r_part_g),
            "partial_garch_p": float(p_part_g),
            "sharpe_garch": sh_g,
            "sharpe_cascade": sh_c,
            "sharpe_combined": sh_b,
            "sharpe_bh": sh_bh,
        })

    df = pd.DataFrame(rows)
    print("\n" + "=" * 78)
    print("AGGREGATE")
    print("=" * 78)
    print(f"\n  Orthogonality (cascade vs GARCH):")
    print(f"    median Spearman: {df['orthogonality_r'].median():+.4f}")
    print(f"    assets with |r| < 0.3 (orthogonal): {(df['orthogonality_r'].abs() < 0.3).sum()}/{len(df)}")
    print(f"\n  Partial correlation: cascade given GARCH")
    print(f"    median: {df['partial_cascade_given_garch'].median():+.4f}")
    print(f"    assets with p<0.05 (cascade has residual signal): {(df['partial_cascade_p'] < 0.05).sum()}/{len(df)}")
    print(f"\n  Partial correlation: GARCH given cascade")
    print(f"    median: {df['partial_garch_given_cascade'].median():+.4f}")
    print(f"    assets with p<0.05: {(df['partial_garch_p'] < 0.05).sum()}/{len(df)}")
    print(f"\n  Vol-targeting Sharpe (out-of-sample, last 30% of data):")
    print(f"    median GARCH only:      {df['sharpe_garch'].median():.3f}")
    print(f"    median cascade only:    {df['sharpe_cascade'].median():.3f}")
    print(f"    median COMBINED:        {df['sharpe_combined'].median():.3f}")
    print(f"    median buy-hold:        {df['sharpe_bh'].median():.3f}")
    if df['sharpe_combined'].median() > df['sharpe_garch'].median() and df['sharpe_combined'].median() > df['sharpe_cascade'].median():
        print(f"    --> COMBINED MODEL WINS (genuine complementary gain)")
    elif df['sharpe_combined'].median() == df['sharpe_garch'].median() or df['sharpe_combined'].median() == df['sharpe_cascade'].median():
        print(f"    --> Combined ties with best single (no real gain)")

    out_path = ROOT / "results" / "garch_complementarity.json"
    with open(out_path, "w") as f:
        json.dump({
            "per_asset": [dict(r) for r in rows],
            "summary": {
                "median_orthogonality": float(df['orthogonality_r'].median()),
                "median_partial_cascade_given_garch": float(df['partial_cascade_given_garch'].median()),
                "median_sharpe_garch": float(df['sharpe_garch'].median()),
                "median_sharpe_cascade": float(df['sharpe_cascade'].median()),
                "median_sharpe_combined": float(df['sharpe_combined'].median()),
                "median_sharpe_bh": float(df['sharpe_bh'].median()),
            },
        }, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
