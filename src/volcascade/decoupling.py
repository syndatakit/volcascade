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
    """Chow F-statistic for a structural break at order k.

    Compares the bivariate regression
        z_sector = alpha + gamma * z_stock + eps
    fit on the full window vs. fit on the window excluding the k-th
    observation. Returns (F, p-value, n_effective).

    The F-statistic is computed as
        F = ((RSS_pooled - RSS_split) / q) / (RSS_split / (n - 2q))
    where q = 2 (number of parameters in each restricted regression)
    and n is the effective sample size.
    """
    from scipy import stats as sps

    y, x = _stack_pair(z_stock, z_sector)
    n = len(y)
    if n < 2 * lookback or k < 1 or k >= n - 1:
        return np.nan, np.nan, n

    # Pooled regression (full window)
    X_full = np.column_stack([np.ones(n), x])
    beta_full, *_ = np.linalg.lstsq(X_full, y, rcond=None)
    rss_pooled = np.sum((y - X_full @ beta_full) ** 2)

    # Split regression (exclude the k-th observation)
    idx = np.concatenate([np.arange(k), np.arange(k + 1, n)])
    y_s, x_s = y[idx], x[idx]
    X_split = np.column_stack([np.ones(len(idx)), x_s])
    beta_split, *_ = np.linalg.lstsq(X_split, y_s, rcond=None)
    rss_split = np.sum((y_s - X_split @ beta_split) ** 2)

    q = 2
    if rss_split <= 0:
        return np.nan, np.nan, n
    f = ((rss_pooled - rss_split) / q) / (rss_split / (n - 2 * q))
    p = 1.0 - sps.f.cdf(f, q, n - 2 * q)
    return float(f), float(p), n


def chow_decoupling(
    z_stock: np.ndarray | pd.Series,
    z_sector: np.ndarray | pd.Series,
    max_order: int = 4,
    lookback: int = 252,
    alpha: float = 0.05,
) -> dict:
    """Identify the decoupling order k* via Chow test.

    The decoupling order is the smallest k in {1, ..., max_order} at which
    the Chow F-test rejects the null of equal conditional distributions
    at significance level ``alpha``. If no k rejects, decoupling_order is
    None (the two series co-move through all orders).

    Parameters
    ----------
    z_stock, z_sector : array-like
        Z-scored order-k series for the stock and its sector benchmark.
    max_order : int
        Maximum order to test. Default 4.
    lookback : int
        Window for the regression. Default 252.
    alpha : float
        Significance level. Default 0.05.

    Returns
    -------
    dict
        Keys: ``decoupling_order`` (int or None), ``f_statistics`` (dict of
        {k: (F, p)}), ``co_moves`` (bool).
    """
    if isinstance(z_stock, pd.Series):
        z_stock = z_stock.to_numpy()
    if isinstance(z_sector, pd.Series):
        z_sector = z_sector.to_numpy()

    fstats: dict[int, tuple[float, float]] = {}
    decoupling_order: int | None = None
    for k in range(1, max_order + 1):
        f, p, n = chow_statistic(z_stock, z_sector, k, lookback=lookback)
        fstats[k] = (f, p)
        if decoupling_order is None and not np.isnan(p) and p < alpha:
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
