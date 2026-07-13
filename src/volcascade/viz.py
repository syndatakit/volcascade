"""Visualization utilities for the volatility cascade.

Provides:
- Cascade plot: 4-panel (one per order) time series with z-score overlay
- Slope heatmap: 2D heatmap of (order, time) z-scores
- Regime overlay: cascade slope + regime flags from HMM/CUSUM baselines
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "plot_cascade",
    "plot_slope",
    "plot_regime_overlay",
]


def plot_cascade(
    cascade: dict[int, pd.DataFrame | pd.Series],
    zcascade: dict[int, pd.DataFrame | pd.Series] | None = None,
    asset: str | None = None,
    ax=None,
):
    """Plot the cascade: one panel per order, with optional z-score overlay.

    Parameters
    ----------
    cascade : dict of {order: array-like}
        Raw cascade (output of :func:`volcascade.cascade.build`).
    zcascade : dict of {order: array-like}, optional
        Z-scored cascade. If provided, overlaid on the right axis.
    asset : str, optional
        Which column to plot. If None and the input is a DataFrame, the
        first column is used.
    ax : matplotlib axis, optional
        If None, a new figure is created.
    """
    import matplotlib.pyplot as plt

    orders = sorted(cascade.keys())
    n = len(orders)
    if ax is None:
        _, axes = plt.subplots(n, 1, figsize=(12, 2.5 * n), sharex=True)
        if n == 1:
            axes = [axes]
    else:
        axes = [ax] * n

    for i, k in enumerate(orders):
        v = cascade[k]
        if isinstance(v, pd.DataFrame):
            v = v[asset] if asset else v.iloc[:, 0]
        axes[i].plot(v.index, v.values, label=f"order {k}", linewidth=0.8)
        axes[i].set_ylabel(f"σ^({k})")
        axes[i].legend(loc="upper right", fontsize=8)
        axes[i].grid(True, alpha=0.3)

        if zcascade is not None and k in zcascade:
            z = zcascade[k]
            if isinstance(z, pd.DataFrame):
                z = z[asset] if asset else z.iloc[:, 0]
            ax2 = axes[i].twinx()
            ax2.plot(z.index, z.values, color="red", alpha=0.4, linewidth=0.5)
            ax2.set_ylabel("z", color="red", fontsize=8)
            ax2.tick_params(axis="y", labelcolor="red", labelsize=7)

    axes[-1].set_xlabel("date")
    return axes


def plot_slope(
    slope_series: pd.DataFrame | pd.Series,
    ax=None,
):
    """Plot the cascade slope (or slope matrix if DataFrame)."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    if isinstance(slope_series, pd.DataFrame):
        for col in slope_series.columns:
            ax.plot(slope_series.index, slope_series[col], label=col, linewidth=0.7)
        ax.legend(fontsize=8, ncol=4)
    else:
        ax.plot(slope_series.index, slope_series.values, linewidth=0.7)
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_ylabel("cascade slope β")
    ax.set_xlabel("date")
    ax.set_title("Volatility cascade slope")
    ax.grid(True, alpha=0.3)
    return ax


def plot_regime_overlay(
    slope_series: pd.DataFrame | pd.Series,
    regime_labels: np.ndarray,
    ax=None,
):
    """Plot cascade slope with regime labels as colored background bands."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    s = slope_series.iloc[:, 0] if isinstance(slope_series, pd.DataFrame) else slope_series
    ax.plot(s.index, s.values, color="black", linewidth=0.7)

    # Shade background by regime
    labels = np.asarray(regime_labels)
    n = len(s)
    if len(labels) == n:
        for i in range(n - 1):
            ax.axvspan(s.index[i], s.index[i + 1], alpha=0.15,
                       color="red" if labels[i] == 1 else "blue")

    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_ylabel("cascade slope β")
    ax.set_xlabel("date")
    ax.legend(handles=[Patch(color="red", alpha=0.3, label="regime 1"),
                       Patch(color="blue", alpha=0.3, label="regime 0")],
              fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    return ax
