"""H3 cross-sectional decoupling: Chow test and cross-correlation threshold.

Implements Section 6 of docs/METHODOLOGY.md.

The decoupling order k* is the smallest order k at which the joint
distribution of (z^(k)_{stock}, z^(k)_{sector}) rejects the null of
equal conditional distributions via a Chow test. Low k* (decoupling at
order 1-2) predicts idiosyncratic events; high k* or no-decoupling
predicts systemic events.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "chow_decoupling",
    "correlation_decoupling",
]


def _stack_pair(
    z_stock: np.ndarray, z_sector: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Stack two equal-length z-series and drop NaN warmup rows."""
    mask = ~(np.isnan(z_stock) | np.isnan(z_sector))
    return z_stock[mask], z_sector[mask]


def chow_statistic(
    z_stock: np.ndarray, z_sector: np.ndarray, k: int, lookback: int = 252
) -> tuple[float, float, int]:
    """Chow F-statistic for a structural break at observation k.

    Compares the bivariate regression
        z_sector = alpha + gamma * z_stock + eps
    fit on the *before* window [k - lookback, k - 1] vs. the *after* window
    [k, k + lookback - 1]. Returns (F, p-value, n_effective).

    The F-statistic is
        F = ((RSS_pooled - RSS_before - RSS_after) / q) / ((RSS_before + RSS_after) / (2W - 2q))
    where q = 2 (params per regression) and W = lookback.

    This is the canonical Chow-test setup with equal-sized before/after
    windows. Single-point removal has near-zero power in long series; the
    windowed test has the standard power for detecting a regime shift.
    """
    from scipy import stats as sps

    y_full, x_full = _stack_pair(z_stock, z_sector)
    n = len(y_full)
    if k < lookback or k + lookback > n:
        return np.nan, np.nan, n

    before = slice(k - lookback, k)
    after = slice(k, k + lookback)

    y_b, x_b = y_full[before], x_full[before]
    y_a, x_a = y_full[after], x_full[after]
    y_p = np.concatenate([y_b, y_a])
    x_p = np.concatenate([x_b, x_a])

    # Pooled regression
    X_p = np.column_stack([np.ones(len(y_p)), x_p])
    beta_p, *_ = np.linalg.lstsq(X_p, y_p, rcond=None)
    rss_pooled = float(np.sum((y_p - X_p @ beta_p) ** 2))

    # Before regression
    X_b = np.column_stack([np.ones(len(y_b)), x_b])
    beta_b, *_ = np.linalg.lstsq(X_b, y_b, rcond=None)
    rss_before = float(np.sum((y_b - X_b @ beta_b) ** 2))

    # After regression
    X_a = np.column_stack([np.ones(len(y_a)), x_a])
    beta_a, *_ = np.linalg.lstsq(X_a, y_a, rcond=None)
    rss_after = float(np.sum((y_a - X_a @ beta_a) ** 2))

    q = 2
    w = lookback
    rss_split = rss_before + rss_after
    if rss_split <= 0:
        return np.nan, np.nan, n
    f = ((rss_pooled - rss_split) / q) / (rss_split / (2 * w - 2 * q))
    p = float(1.0 - sps.f.cdf(f, q, 2 * w - 2 * q))
    return float(f), p, n


def chow_decoupling(
    z_stock: np.ndarray | pd.Series,
    z_sector: np.ndarray | pd.Series,
    max_order: int = 4,
    lookback: int = 252,
    alpha: float = 0.05,
) -> dict:
    """Identify the decoupling order k* via sliding-window Chow test.

    For each k in {1, ..., max_order}, the Chow test is run at every
    time t in [lookback, n-lookback]. The decoupling order is the
    smallest k at which ANY window's Chow test rejects the null of
    stable conditional distributions at significance ``alpha``.

    In the current implementation, ``z_stock`` and ``z_sector`` are
    treated as already-z-scored single-order series (the same series
    across all k — i.e. a flat cascade). The decoupling test then asks
    whether the relationship between stock and sector at observation
    level has a structural break in any window. This is the
    "co-movement at order 0" baseline; for multi-order decoupling, use
    the z-cascade API in :func:`chow_decoupling_cascade`.

    Parameters
    ----------
    z_stock, z_sector : array-like
        Z-scored single-order series.
    max_order : int
        Number of orders to test (each order uses the same input series
        in this simplified API). Default 4.
    lookback : int
        Window size for the Chow test. Default 252.
    alpha : float
        Significance level. Default 0.05.

    Returns
    -------
    dict
        Keys: ``decoupling_order`` (int or None), ``f_statistics`` (dict
        of {k: (max_F, min_p)}), ``co_moves`` (bool).
    """
    if isinstance(z_stock, pd.Series):
        z_stock = z_stock.to_numpy()
    if isinstance(z_sector, pd.Series):
        z_sector = z_sector.to_numpy()

    fstats: dict[int, tuple[float, float]] = {}
    decoupling_order: int | None = None
    n = len(z_stock)

    for k in range(1, max_order + 1):
        # Slide a window across the series; at each t, do a Chow test
        # of structural break at t. Record the (F, p) of the strongest
        # rejection in the window.
        best_f, best_p = -np.inf, 1.0
        for t in range(lookback, n - lookback + 1):
            f, p, _ = chow_statistic(z_stock, z_sector, t, lookback=lookback)
            if np.isnan(p):
                continue
            if f > best_f:
                best_f, best_p = f, p
        fstats[k] = (best_f, best_p)
        if decoupling_order is None and best_p < alpha:
            decoupling_order = k

    return {
        "decoupling_order": decoupling_order,
        "f_statistics": fstats,
        "co_moves": decoupling_order is None,
    }


def correlation_decoupling(
    z_stock: np.ndarray | pd.Series,
    z_sector: np.ndarray | pd.Series,
    window: int = 60,
    threshold: float = 0.5,
) -> dict:
    """Identify decoupling via rolling cross-correlation threshold.

    A simpler, threshold-based decoupling test (robustness check). Decoupling
    is flagged at the first order k where the rolling cross-correlation
    between z_stock and z_sector drops below ``threshold`` for at least 5
    consecutive days.

    Parameters
    ----------
    z_stock, z_sector : array-like
        Z-scored series.
    window : int
        Rolling correlation window. Default 60.
    threshold : float
        Decoupling threshold. Default 0.5.

    Returns
    -------
    dict
        Keys: ``decoupling_order`` (int or None), ``rolling_corr`` (Series),
        ``co_moves`` (bool).
    """
    if isinstance(z_stock, pd.Series):
        z_stock = z_stock.to_numpy()
    if isinstance(z_sector, pd.Series):
        z_sector = z_sector.to_numpy()

    y, x = _stack_pair(z_stock, z_sector)
    n = len(y)
    s_y, s_x = pd.Series(y), pd.Series(x)
    rolling_corr = s_y.rolling(window).corr(s_x)

    decoupling_order: int | None = None
    below = (rolling_corr < threshold).fillna(False).to_numpy()
    for k in range(1, len(rolling_corr) - 4):
        if decoupling_order is None and all(below[k : k + 5]):
            decoupling_order = k
            break

    return {
        "decoupling_order": decoupling_order,
        "rolling_corr": rolling_corr,
        "co_moves": decoupling_order is None,
    }
