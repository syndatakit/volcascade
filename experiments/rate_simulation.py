"""Cascade slope consistency-rate simulation.

Empirical check on the variance scaling of the cascade slope estimator.
The paper's theory claims Var(beta_hat_t) ~ w^-1 (where w is the cascade window).
This script sweeps w and L (z-score lookback) independently, computes the
empirical variance of beta_hat across Monte Carlo replications, and fits
the log-log slope of Var vs w and Var vs L.

Method:
- Generate AR(1) log returns with rho = 0.3, sigma = 0.01 (alpha-mixing stand-in)
- T = 5000 time steps, evaluate beta_hat at t = 4500 (well past all warmups)
- N_SIM = 500 Monte Carlo replications
- Cascade: V^1 = rolling std of returns (window w), V^k = rolling std of V^(k-1)
- z-score: mean/std over past L values [t-L, t-1] (strict past, shift-by-one)
- Cascade slope: OLS of (1, 2, 3, 4) on (z^1, z^2, z^3, z^4) at time t
- Empirical Var(beta_hat) over N_SIM replications

Run: python rate_simulation.py
Output: sim_results.json + printed summary
"""

import json
import os
import warnings

import numpy as np

warnings.filterwarnings("ignore")
np.random.seed(42)


def rolling_std_nan_safe(X, w):
    """Rolling std that handles NaN in X by skipping NaN within each window."""
    N, T = X.shape
    out = np.full((N, T), np.nan)
    is_valid = np.isfinite(X).astype(float)
    X_filled = np.where(np.isfinite(X), X, 0.0)
    c1 = np.cumsum(np.insert(X_filled, 0, 0.0, axis=1), axis=1)
    c2 = np.cumsum(np.insert(X_filled ** 2, 0, 0.0, axis=1), axis=1)
    cv = np.cumsum(np.insert(is_valid, 0, 0.0, axis=1), axis=1)
    for i in range(T):
        if i < w - 1:
            continue
        s = c1[:, i + 1] - c1[:, i + 1 - w]
        s2 = c2[:, i + 1] - c2[:, i + 1 - w]
        n = cv[:, i + 1] - cv[:, i + 1 - w]
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = np.where(n > 0, s / np.maximum(n, 1), 0.0)
            var = np.maximum(s2 / np.maximum(n, 1) - mean ** 2, 0.0)
            sd = np.where(n > 1, np.sqrt(var * n / np.maximum(n - 1, 1)), np.nan)
        out[:, i] = sd
    return out


def zscore_vec(S, L):
    """Z-score using past L values [t-L, t-1] (strict past, shift-by-one)."""
    N, T = S.shape
    c1 = np.where(np.isfinite(S), S, 0.0)
    c1 = np.cumsum(c1, axis=1)
    c2 = np.where(np.isfinite(S), S ** 2, 0.0)
    c2 = np.cumsum(c2, axis=1)
    cnt = np.cumsum(np.isfinite(S).astype(int), axis=1)
    out = np.full((N, T), np.nan)
    for t in range(L, T):
        s_t = c1[:, t - 1] - (c1[:, t - L - 1] if t - L - 1 >= 0 else 0)
        s2_t = c2[:, t - 1] - (c2[:, t - L - 1] if t - L - 1 >= 0 else 0)
        n_t = cnt[:, t - 1] - (cnt[:, t - L - 1] if t - L - 1 >= 0 else 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = np.where(n_t > 0, s_t / np.maximum(n_t, 1), np.nan)
            var = np.maximum(s2_t / np.maximum(n_t, 1) - mean ** 2, 0.0)
            sd = np.sqrt(var * n_t / np.maximum(n_t - 1, 1))
            z = np.where((sd > 0) & np.isfinite(S[:, t]), (S[:, t] - mean) / sd, np.nan)
        out[:, t] = z
    return out


def cascade_slope_at_t(returns, w, L, t, K=4):
    V = [None] * (K + 1)
    V[1] = rolling_std_nan_safe(returns, w)
    for k in range(2, K + 1):
        V[k] = rolling_std_nan_safe(V[k - 1], w)
    z = [zscore_vec(V[k], L) for k in range(1, K + 1)]
    z_t = np.stack([z[k][:, t] for k in range(4)], axis=1)
    finite = np.all(np.isfinite(z_t), axis=1)
    k_arr = np.array([1.0, 2.0, 3.0, 4.0])
    k_centered = k_arr - k_arr.mean()
    den = (k_centered ** 2).sum()
    z_centered = z_t - z_t.mean(axis=1, keepdims=True)
    slope = np.full(z_t.shape[0], np.nan)
    slope[finite] = (k_centered * z_centered[finite]).sum(axis=1) / den
    return slope


def main():
    N_SIM = 500
    T_TOTAL = 5000
    RHO = 0.3
    SIGMA_EPS = 0.01
    T_EVAL = 4500

    print("Pre-generating return series...")
    returns_all = np.zeros((N_SIM, T_TOTAL))
    eps = np.random.randn(N_SIM, T_TOTAL) * SIGMA_EPS
    for t in range(1, T_TOTAL):
        returns_all[:, t] = RHO * returns_all[:, t - 1] + eps[:, t]
    print(f"  done. shape={returns_all.shape}")
    print()

    print("=" * 80)
    print("SWEEP w (cascade window) at L=252")
    print("=" * 80)
    W_VALUES = [5, 10, 20, 40, 80, 160]
    results_w = {}
    for w in W_VALUES:
        betas = cascade_slope_at_t(returns_all, w=w, L=252, t=T_EVAL)
        finite = betas[np.isfinite(betas)]
        var_b = float(finite.var(ddof=1))
        results_w[w] = {"var": var_b, "mean": float(finite.mean()), "n_valid": int(len(finite))}
        print(f"  w={w:>4d}: Var(beta_hat) = {var_b:.6e}, mean = {finite.mean():+.4f}, n = {len(finite)}")
    print()

    print("=" * 80)
    print("SWEEP L (z-score lookback) at w=21")
    print("=" * 80)
    L_VALUES = [60, 120, 252, 504, 1008]
    results_L = {}
    for L in L_VALUES:
        betas = cascade_slope_at_t(returns_all, w=21, L=L, t=T_EVAL)
        finite = betas[np.isfinite(betas)]
        var_b = float(finite.var(ddof=1))
        results_L[L] = {"var": var_b, "mean": float(finite.mean()), "n_valid": int(len(finite))}
        print(f"  L={L:>4d}: Var(beta_hat) = {var_b:.6e}, mean = {finite.mean():+.4f}, n = {len(finite)}")
    print()

    print("=" * 80)
    print("LOG-LOG SLOPES")
    print("=" * 80)
    ws = np.array(sorted(results_w.keys()))
    vs_w = np.array([results_w[w]["var"] for w in ws])
    mask = (vs_w > 0) & np.isfinite(vs_w) & (vs_w > 0)
    if mask.sum() >= 2:
        slope_w = np.polyfit(np.log(ws[mask]), np.log(vs_w[mask]), 1)[0]
        print(f"  Var vs w:  slope = {slope_w:+.3f}  (paper claims -1)")
    else:
        slope_w = np.nan

    Ls = np.array(sorted(results_L.keys()))
    vs_L = np.array([results_L[L]["var"] for L in Ls])
    mask = (vs_L > 0) & np.isfinite(vs_L) & (vs_L > 0)
    if mask.sum() >= 2:
        slope_L = np.polyfit(np.log(Ls[mask]), np.log(vs_L[mask]), 1)[0]
        print(f"  Var vs L:  slope = {slope_L:+.3f}  (if L is rate-limiting, should be -1)")
    else:
        slope_L = np.nan

    print()
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print(f"  Observed log-log slope in w: {slope_w:+.3f}")
    print(f"  Observed log-log slope in L: {slope_L:+.3f}")
    if slope_w == slope_w:
        if abs(slope_w + 1) < 0.2:
            print(f"  -> Var(beta_hat) scales like w^-1 (consistent with paper's claim).")
        elif slope_w > -0.3:
            print(f"  -> Var(beta_hat) does NOT shrink in w (slope = {slope_w:+.3f}, near 0). Paper's w^-1 claim is NOT supported by simulation.")
        else:
            print(f"  -> Var(beta_hat) shrinks in w but slower than w^-1 (slope = {slope_w:+.3f}).")
    if slope_L == slope_L:
        if abs(slope_L + 1) < 0.2:
            print(f"  -> Var(beta_hat) scales like L^-1. L is the rate-limiting variable.")
        elif slope_L > -0.3:
            print(f"  -> Var(beta_hat) does NOT shrink in L (slope = {slope_L:+.3f}). L is not the rate-limiting variable.")
        else:
            print(f"  -> Var(beta_hat) shrinks in L but slower than L^-1.")

    summary = {
        "sweep_w_at_L252": {str(k): v for k, v in results_w.items()},
        "sweep_L_at_w21": {str(k): v for k, v in results_L.items()},
        "log_log_slope_var_vs_w": float(slope_w) if slope_w == slope_w else None,
        "log_log_slope_var_vs_L": float(slope_L) if slope_L == slope_L else None,
        "n_sim": N_SIM,
        "T_total": T_TOTAL,
        "T_eval": T_EVAL,
        "rho": RHO,
        "sigma_eps": SIGMA_EPS,
        "method": "AR(1) with rho=0.3, sigma=0.01, 500 Monte Carlo replications, evaluate at t=4500 of a 5000-step series. NaN-safe rolling std (skips NaN within window) and z-score (uses past L values [t-L, t-1])."
    }
    os.makedirs("results", exist_ok=True)
    with open("results/sim_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print()
    print("Saved results/sim_results.json")


if __name__ == "__main__":
    main()
