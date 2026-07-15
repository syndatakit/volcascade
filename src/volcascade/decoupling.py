"""H3 cross-sectional decoupling analysis.

Two API functions for testing whether two cascade series (e.g., a stock
and its sector) decouple at one or more differentiation orders:

- chow_decoupling: tests decoupling on a single z-scored series
  ("flat cascade baseline"). Returns the smallest k* where ANY window
  rejects the null at significance alpha, where the same z-series is
  used for all k.

- chow_decoupling_cascade: tests decoupling across cascade orders
  1..K by running a sliding-window Chow test on each order's z-scored
  series independently. Returns the smallest k* where ANY window
  rejects at significance alpha. This is the API that formalizes the
  per-order Chow test used in the H3 v3-v5 experiment scripts.

Plus the low-level helper:

- chow_statistic: compute the Chow F-statistic at a specific breakpoint
  k with a window of length lookback on either side.

Interpretation
--------------
- Low k* (1-2): decoupling at the high-frequency / vol level.
- High k* (3-4): decoupling at the vol-of-vol level.
- None (co_moves=True): the stock and sector co-move across all orders.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "chow_decoupling",
    "chow_decoupling_cascade",
    "chow_statistic",
    "correlation_decoupling",
]


def chow_statistic(z_stock, z_sector, k, lookback=252):
    """Compute Chow F-statistic for a structural break at observation k.

    Compares a bivariate regression ``z_sector = alpha + gamma * z_stock + eps``
    before window ``[k - lookback, k - 1]`` vs after window
    ``[k, k + lookback - 1]`` using equal-sized windows.

    Parameters
    ----------
    z_stock, z_sector : array-like
        Paired time series of z-scored cascade values.
    k : int
        Breakpoint index. Must satisfy ``lookback <= k <= n - lookback``.
    lookback : int
        Window size on either side of the breakpoint (default 252).

    Returns
    -------
    (F, p, n_eff) : tuple
        F-statistic, p-value, and effective sample size. Returns
        ``(np.nan, np.nan, n)`` if k is out of range.
    """
    z = _stack_pair(z_stock, z_sector)
    if z is None:
        n = len(np.atleast_1d(z_stock))
        return (np.nan, np.nan, n)
    n = len(z["x"])
    if k < lookback or k + lookback > n:
        return (np.nan, np.nan, n)

    q = 2  # parameters per regression
    W = lookback
    x1 = z["x"][k - W:k]
    y1 = z["y"][k - W:k]
    x2 = z["x"][k:k + W]
    y2 = z["y"][k:k + W]

    def _betas(x, y):
        X = np.column_stack([np.ones_like(x), x])
        return np.linalg.lstsq(X, y, rcond=None)[0]

    b_full = _betas(z["x"], z["y"])
    y_hat_full = b_full[0] + b_full[1] * z["x"]
    rss_full = float(np.sum((z["y"] - y_hat_full) ** 2))

    b1 = _betas(x1, y1)
    rss1 = float(np.sum((y1 - (b1[0] + b1[1] * x1)) ** 2))
    b2 = _betas(x2, y2)
    rss2 = float(np.sum((y2 - (b2[0] + b2[1] * x2)) ** 2))

    rss_pooled = rss_full
    rss_unpooled = rss1 + rss2
    df_num = q
    df_den = 2 * W - 2 * q
    if rss_unpooled <= 0 or df_den <= 0:
        return (np.nan, np.nan, n)
    F = ((rss_pooled - rss_unpooled) / df_num) / (rss_unpooled / df_den)
    from scipy.stats import f as f_dist
    p = 1.0 - float(f_dist.cdf(F, df_num, df_den))
    return (float(F), float(p), int(n))


def chow_decoupling(z_stock, z_sector, max_order=4, lookback=252, alpha=0.05):
    """Identify decoupling order k* on a single z-scored series.

    Sliding-window Chow test at a single breakpoint (the midpoint of the
    series). Tests the null that the bivariate regression between stock
    and sector z-scores is stable across the window. ``k*`` is set to 1
    if the Chow test rejects at the midpoint at significance ``alpha``.

    IMPORTANT: this is the "flat cascade baseline" — the same z-series
    is used regardless of order. For per-order decoupling across the
    cascade (the H3 v3-v5 methodology), use
    :func:`chow_decoupling_cascade` instead.

    Parameters
    ----------
    z_stock, z_sector : array-like
        Paired z-scored series.
    max_order : int
        Included for API parity; the function only tests a single order.
        Use :func:`chow_decoupling_cascade` for the multi-order version.
    lookback : int
        Window size on either side of the midpoint (default 252).
    alpha : float
        Significance level (default 0.05).

    Returns
    -------
    dict
        Keys: ``decoupling_order`` (int or None), ``f_statistics`` (dict
        of {order: (F, p)}), ``co_moves`` (bool).
    """
    z = _stack_pair(z_stock, z_sector)
    if z is None or len(z["x"]) < 2 * lookback:
        return {
            "decoupling_order": None,
            "f_statistics": {k: (np.nan, np.nan) for k in range(1, max_order + 1)},
            "co_moves": True,
        }

    n = len(z["x"])
    mid = n // 2
    F, p, _ = chow_statistic(z["x"], z["y"], mid, lookback=lookback)

    f_statistics = {
        1: (float(F) if not np.isnan(F) else np.nan,
            float(p) if not np.isnan(p) else np.nan)
    }
    for k in range(2, max_order + 1):
        # Without per-order z-series, only order 1 has a real test.
        f_statistics[k] = (np.nan, np.nan)

    decoupling_order = 1 if (not np.isnan(p) and p < alpha) else None

    return {
        "decoupling_order": decoupling_order,
        "f_statistics": f_statistics,
        "co_moves": decoupling_order is None,
    }


def chow_decoupling_cascade(
    z_cascade_stock: dict,
    z_cascade_sector: dict,
    max_order: int = 4,
    lookback: int = 252,
    alpha: float = 0.05,
    n_windows: int = 20,
) -> dict:
    """Identify decoupling order k* across cascade orders 1..max_order.

    For each order k in {1, ..., max_order}, runs a sliding-window Chow
    test on the per-order z-scored series. The decoupling order is the
    smallest k where ANY window rejects the null at significance alpha.

    This is the formalization of the per-order Chow test used in the H3
    v3-v5 experiment scripts. The v3-v5 scripts call
    :func:`chow_statistic` directly at a single midpoint per order; this
    function provides a sliding-window API consistent with
    :func:`chow_decoupling`.

    Parameters
    ----------
    z_cascade_stock : dict
        Z-scored cascade for the stock. Keys are integer orders
        (1, 2, ...); values are pd.Series or np.ndarray.
    z_cascade_sector : dict
        Z-scored cascade for the sector or index, same structure.
    max_order : int
        Maximum order to test (default 4).
    lookback : int
        Window size for the Chow test (default 252).
    alpha : float
        Significance level (default 0.05).
    n_windows : int
        Maximum number of sliding windows per order (default 20). The
        actual count is ``min(n_windows, n - 2*lookback)``.

    Returns
    -------
    dict
        Keys:
        - ``decoupling_order``: int or None. Smallest k where ANY window
          rejects the null at significance alpha; None if no order
          shows significant decoupling.
        - ``f_statistics``: dict of ``{k: (max_F, min_p, n_eff)}``.
        - ``co_moves``: bool. True if no decoupling detected.
    """
    expected_orders = set(range(1, max_order + 1))
    missing_stock = expected_orders - set(z_cascade_stock.keys())
    missing_sector = expected_orders - set(z_cascade_sector.keys())
    if missing_stock:
        raise ValueError(
            f"z_cascade_stock missing orders {sorted(missing_stock)}; "
            f"got {sorted(z_cascade_stock.keys())}"
        )
    if missing_sector:
        raise ValueError(
            f"z_cascade_sector missing orders {sorted(missing_sector)}; "
            f"got {sorted(z_cascade_sector.keys())}"
        )

    f_statistics: dict = {}
    decoupling_order = None

    for k in range(1, max_order + 1):
        z_s = _stack_pair(z_cascade_stock[k], z_cascade_sector[k])
        if z_s is None or len(z_s["x"]) < 2 * lookback:
            f_statistics[k] = (np.nan, np.nan, 0)
            continue

        n = len(z_s["x"])
        step = max(1, (n - 2 * lookback) // n_windows)
        windows = list(range(lookback, n - lookback, step))
        if not windows:
            windows = [n // 2]  # fallback: single midpoint

        min_p = np.inf
        max_F = -np.inf
        n_eff_total = 0

        for k_idx in windows:
            F, p, n_eff = chow_statistic(
                z_s["x"], z_s["y"], k_idx, lookback=lookback
            )
            if not np.isnan(p) and p < min_p:
                min_p = p
                max_F = F
                n_eff_total = n_eff

        f_statistics[k] = (
            float(max_F) if max_F > -np.inf else np.nan,
            float(min_p) if min_p < np.inf else np.nan,
            int(n_eff_total),
        )

        if decoupling_order is None and min_p < alpha:
            decoupling_order = k

    return {
        "decoupling_order": decoupling_order,
        "f_statistics": f_statistics,
        "co_moves": decoupling_order is None,
    }


def correlation_decoupling(z_stock, z_sector, window=60, threshold=0.5):
    """Decoupling via rolling cross-correlation threshold.

    Robustness check on :func:`chow_decoupling`. Computes rolling
    cross-correlation between z_stock and z_sector. Flags decoupling
    when the correlation drops below ``threshold`` for at least 5
    consecutive days.

    Parameters
    ----------
    z_stock, z_sector : array-like
        Paired z-scored series.
    window : int
        Rolling correlation window (default 60).
    threshold : float
        Correlation below this is flagged as decoupling (default 0.5).

    Returns
    -------
    dict
        Keys: ``decoupling_order`` (int or None), ``rolling_corr``
        (pd.Series), ``co_moves`` (bool).
    """
    if isinstance(z_stock, pd.Series):
        z_s = z_stock.to_numpy()
    else:
        z_s = np.asarray(z_stock, dtype=float)
    if isinstance(z_sector, pd.Series):
        z_b = z_sector.to_numpy()
    else:
        z_b = np.asarray(z_sector, dtype=float)

    n = min(len(z_s), len(z_b))
    if n < window:
        return {
            "decoupling_order": None,
            "rolling_corr": pd.Series(dtype=float),
            "co_moves": True,
        }

    z_s = z_s[:n]
    z_b = z_b[:n]

    df = pd.DataFrame({"s": z_s, "b": z_b}).dropna()
    rolling_corr = df["s"].rolling(window, min_periods=window // 2).corr(df["b"])

    below = (rolling_corr < threshold).fillna(False).to_numpy()
    run = 0
    decoupling_idx = None
    for i, b in enumerate(below):
        if b:
            run += 1
            if run >= 5 and decoupling_idx is None:
                decoupling_idx = i - 4
        else:
            run = 0

    co_moves = decoupling_idx is None
    return {
        "decoupling_order": 1 if not co_moves else None,
        "rolling_corr": rolling_corr,
        "co_moves": co_moves,
    }


def _stack_pair(z_stock, z_sector):
    """Stack two equal-length z-series and drop NaN warmup rows.

    Returns a dict with keys ``"x"`` and ``"y"`` (paired numpy arrays),
    or None if inputs cannot be aligned.
    """
    if isinstance(z_stock, pd.Series):
        s = z_stock.to_numpy()
    else:
        s = np.asarray(z_stock, dtype=float)
    if isinstance(z_sector, pd.Series):
        b = z_sector.to_numpy()
    else:
        b = np.asarray(z_sector, dtype=float)

    n = min(len(s), len(b))
    if n == 0:
        return None
    s = s[:n]
    b = b[:n]

    mask = ~(np.isnan(s) | np.isnan(b))
    if not mask.any():
        return None
    return {
        "x": s[mask],
        "y": b[mask],
    }
