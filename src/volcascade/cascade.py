"""Core cascade construction: orders 1-N of realized volatility, z-scoring, slope.

Implements Sections 1-3 of docs/METHODOLOGY.md.

The recursive construction is:
    sigma^(1) = realized volatility of returns
    sigma^(k) = rolling sample std of sigma^(k-1), for k >= 2

Each order is then z-scored against its trailing history of length Z, and
the cascade slope is the OLS coefficient from regressing order index on
z-scored volatilities.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "build",
    "zscore",
    "slope",
    "entropy",
]


def _rolling_sample_std(x: np.ndarray, window: int) -> np.ndarray:
    """Rolling sample standard deviation, with min_periods=window (no NaN padding)."""
    x = np.asarray(x)
    if x.ndim == 1:
        s = pd.Series(x)
        return s.rolling(window=window, min_periods=window).std().to_numpy()
    df = pd.DataFrame(x)
    return df.rolling(window=window, min_periods=window).std().to_numpy()


def build(
    returns: pd.DataFrame | pd.Series | np.ndarray,
    orders: tuple[int, ...] = (1, 2, 3, 4),
    inner_window: int = 20,
) -> dict[int, pd.DataFrame | pd.Series]:
    """Construct the volatility cascade: orders 1..N of realized volatility.

    Parameters
    ----------
    returns : DataFrame, Series, or ndarray
        Log-returns. If DataFrame, each column is an asset and the cascade
        is computed per asset. The index is treated as a time axis.
    orders : tuple of int
        Which orders to compute. Must contain 1. Default (1, 2, 3, 4).
    inner_window : int
        Length of the rolling window for each order's sample std. Default 20
        (one trading month). The realized volatility at order 1 uses this
        same window on squared returns.

    Returns
    -------
    dict of {order: DataFrame or Series}
        Keys are the requested orders. Each value has the same shape as the
        input. The first ``(orders.max() - 1) * inner_window`` rows are NaN
        (warmup).
    """
    if 1 not in orders:
        raise ValueError("orders must contain 1")

    is_series = isinstance(returns, pd.Series)
    series_name = returns.name if is_series else None

    if isinstance(returns, np.ndarray):
        returns = pd.DataFrame(returns)
    if is_series:
        returns = returns.to_frame()

    # Order 1: realized vol = sqrt(sum of squared returns over rolling window)
    sq = returns.pow(2)
    rv1 = sq.rolling(window=inner_window, min_periods=inner_window).sum().pow(0.5)

    out: dict[int, pd.DataFrame | pd.Series] = {1: rv1}
    prev = rv1.to_numpy()

    for k in range(2, max(orders) + 1):
        # Order k: rolling sample std of order (k-1)
        current = _rolling_sample_std(prev, inner_window)
        out[k] = current
        prev = current

    # Re-wrap into the original input type (Series vs DataFrame)
    wrapped: dict[int, pd.DataFrame | pd.Series] = {}
    for k in orders:
        v = out[k]
        arr = np.asarray(v)
        if is_series:
            # Squeeze 2D (n,1) result of rolling on a single-column DataFrame
            arr = arr.ravel() if arr.ndim > 1 else arr
            wrapped[k] = pd.Series(arr, index=returns.index, name=series_name)
        else:
            wrapped[k] = pd.DataFrame(arr, index=returns.index, columns=returns.columns)
    return wrapped


def zscore(
    cascade: dict[int, pd.DataFrame | pd.Series],
    lookback: int = 252,
) -> dict[int, pd.DataFrame | pd.Series]:
    """Z-score each order of the cascade against its trailing history.

    Parameters
    ----------
    cascade : dict of {order: array-like}
        Output of :func:`build`. Each value is a DataFrame or Series of raw
        (non-z-scored) cascade values.
    lookback : int
        Z-score lookback in trading days. Default 252 (one calendar year).
        The mean and std are computed on [t-lookback, t-1] (strictly past).

    Returns
    -------
    dict of {order: array-like}
        Z-scored cascade. Same shape as input. The first ``lookback`` rows
        are NaN.
    """
    out: dict[int, pd.DataFrame | pd.Series] = {}
    for k, vol in cascade.items():
        if isinstance(vol, pd.DataFrame):
            mu = vol.rolling(window=lookback, min_periods=lookback).mean().shift(1)
            sd = vol.rolling(window=lookback, min_periods=lookback).std().shift(1)
            out[k] = (vol - mu) / sd
        else:
            s = pd.Series(vol)
            mu = s.rolling(window=lookback, min_periods=lookback).mean().shift(1)
            sd = s.rolling(window=lookback, min_periods=lookback).std().shift(1)
            out[k] = (s - mu) / sd
    return out


def slope(
    zcascade: dict[int, pd.DataFrame | pd.Series],
) -> pd.DataFrame | pd.Series:
    """Cascade slope: OLS coefficient of order index on z-scored volatilities.

    A positive slope means higher orders move more (steepening cascade /
    instability-of-instability). A negative slope means higher orders move
    less (inverted cascade / mean-reversion of vol-of-vol). Near-zero is flat.

    Parameters
    ----------
    zcascade : dict of {order: array-like}
        Output of :func:`zscore`. Must contain orders 1..N for N >= 2.

    Returns
    -------
    DataFrame or Series
        Same shape (minus columns) as a single order. The cascade slope is
        a one-number-per-t summary. Warmup rows are NaN.
    """
    orders = sorted(zcascade.keys())
    if len(orders) < 2:
        raise ValueError("need at least 2 orders to compute slope")

    k = np.asarray(orders, dtype=float)
    k_centered = k - k.mean()

    # Stack z-scores: shape (T, n_orders) per asset (column)
    sample = next(iter(zcascade.values()))
    if isinstance(sample, pd.DataFrame):
        index = sample.index
        columns = sample.columns
        zmat = np.stack([zcascade[o].to_numpy() for o in orders], axis=-1)
        # OLS slope: sum_k (k - kbar)(z_k - zbar) / sum_k (k - kbar)^2
        with np.errstate(invalid="ignore"):
            zbar = np.nanmean(zmat, axis=-1, keepdims=True)
            num = np.nansum((k_centered * (zmat - zbar)), axis=-1)
        # Rows that are all-NaN should produce NaN, not 0
        all_nan = np.all(np.isnan(zmat), axis=-1)
        num = np.where(all_nan, np.nan, num)
        den = np.sum(k_centered ** 2)
        result = pd.DataFrame(num / den, index=index, columns=columns)
    else:
        index = sample.index
        zmat = np.stack([np.asarray(zcascade[o]) for o in orders], axis=-1)
        with np.errstate(invalid="ignore"):
            zbar = np.nanmean(zmat, axis=-1, keepdims=True)
            num = np.nansum((k_centered * (zmat - zbar)), axis=-1)
        all_nan = np.all(np.isnan(zmat), axis=-1)
        num = np.where(all_nan, np.nan, num)
        den = np.sum(k_centered ** 2)
        result = pd.Series(num / den, index=index)

    return result


def entropy(
    zcascade: dict[int, pd.DataFrame | pd.Series],
) -> pd.DataFrame | pd.Series:
    """Cascade entropy: Shannon entropy of the |z|-weighted order distribution.

    A non-linear summary of cascade shape. High entropy = orders are
    evenly weighted (flat cascade). Low entropy = one order dominates.
    Bounded above by ``log(n_orders)``.

    Parameters
    ----------
    zcascade : dict of {order: array-like}
        Output of :func:`zscore`.

    Returns
    -------
    DataFrame or Series
        Cascade entropy per t. Same shape as a single order.
    """
    orders = sorted(zcascade.keys())
    sample = next(iter(zcascade.values()))

    if isinstance(sample, pd.DataFrame):
        zmat = np.stack([np.abs(zcascade[o].to_numpy()) for o in orders], axis=-1)
        total = zmat.sum(axis=-1, keepdims=True)
        p = np.where(total > 0, zmat / np.where(total == 0, 1, total), 1.0 / len(orders))
        # Clip to avoid log(0)
        p = np.clip(p, 1e-12, 1.0)
        h = -np.sum(p * np.log(p), axis=-1)
        return pd.DataFrame(h, index=sample.index, columns=sample.columns)
    else:
        zmat = np.stack([np.abs(np.asarray(zcascade[o])) for o in orders], axis=-1)
        total = zmat.sum(axis=-1, keepdims=True)
        p = np.where(total > 0, zmat / np.where(total == 0, 1, total), 1.0 / len(orders))
        p = np.clip(p, 1e-12, 1.0)
        h = -np.sum(p * np.log(p), axis=-1)
        return pd.Series(h, index=sample.index)
