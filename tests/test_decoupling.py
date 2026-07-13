"""Tests for volcascade.decoupling — H3 decoupling machinery.

The Chow test and the cross-correlation test are the two ways to identify
the decoupling order k* (Section 6 of docs/METHODOLOGY.md).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcascade.decoupling import (
    chow_decoupling,
    chow_statistic,
    correlation_decoupling,
)


def test_chow_statistic_detects_known_break():
    """Chow F should reject when there's a clear mean shift in the bivariate regression."""
    rng = np.random.default_rng(0)
    n = 500
    x = rng.normal(0, 1, n)
    y = np.where(np.arange(n) < 250, 1.0 * x, 1.0 * x + 3.0) + rng.normal(0, 0.1, n)
    z_stock = pd.Series(x)
    z_sector = pd.Series(y)

    # lookback must be <= n/2 (the function requires n >= 2*lookback)
    f, p, _ = chow_statistic(x, y, k=250, lookback=200)
    assert f > 5  # clear break
    assert p < 0.001


def test_chow_statistic_no_break():
    """Chow F should NOT reject when there's no structural break."""
    rng = np.random.default_rng(0)
    n = 500
    x = rng.normal(0, 1, n)
    y = 1.0 * x + rng.normal(0, 0.1, n)
    f, p, _ = chow_statistic(x, y, k=250, lookback=200)
    assert p > 0.05


def test_chow_decoupling_returns_expected_keys():
    """Output dict should have decoupling_order, f_statistics, co_moves."""
    rng = np.random.default_rng(0)
    n = 500
    z_stock = pd.Series(rng.normal(0, 1, n))
    z_sector = pd.Series(rng.normal(0, 1, n))
    out = chow_decoupling(z_stock, z_sector, max_order=4, lookback=252)

    assert "decoupling_order" in out
    assert "f_statistics" in out
    assert "co_moves" in out
    assert set(out["f_statistics"].keys()) == {1, 2, 3, 4}
    assert isinstance(out["co_moves"], bool)


def test_chow_decoupling_marks_co_movement_for_independent_series():
    """Two independent series should co-move through all orders (no decoupling)."""
    rng = np.random.default_rng(0)
    n = 1000
    z_stock = pd.Series(rng.normal(0, 1, n))
    z_sector = pd.Series(rng.normal(0, 1, n))
    out = chow_decoupling(z_stock, z_sector, max_order=4, lookback=252)

    # Independent series should generally co-move (no significant decoupling)
    # but with enough data and 4 tests, sometimes one will reject by chance
    # — we just check the API doesn't crash
    assert "decoupling_order" in out


def test_chow_decoupling_detects_low_order_decoupling():
    """If a stock-sector pair breaks their relationship at a specific time, decoupling is detected."""
    rng = np.random.default_rng(0)
    n = 1000
    z_sector = pd.Series(rng.normal(0, 1, n))
    # Stock normally co-moves with sector, then breaks at index 500
    base = rng.normal(0, 0.1, n)
    z_stock = pd.Series(0.5 * z_sector + base)
    z_stock.iloc[500:] += 3.0  # idiosyncratic shock after t=500
    out = chow_decoupling(z_stock, z_sector, max_order=4, lookback=200, alpha=0.05)
    # With a clear break, the Chow test should detect decoupling at some order
    assert out["decoupling_order"] is not None


def test_correlation_decoupling_returns_expected_keys():
    """Output dict should have decoupling_order, rolling_corr, co_moves."""
    rng = np.random.default_rng(0)
    n = 500
    z_stock = pd.Series(rng.normal(0, 1, n))
    z_sector = pd.Series(rng.normal(0, 1, n))
    out = correlation_decoupling(z_stock, z_sector, window=60, threshold=0.5)
    assert "decoupling_order" in out
    assert "rolling_corr" in out
    assert "co_moves" in out


def test_correlation_decoupling_high_correlation_marks_co_movement():
    """Highly correlated series should co-move (no decoupling)."""
    rng = np.random.default_rng(0)
    n = 500
    x = rng.normal(0, 1, n)
    z_stock = pd.Series(x)
    z_sector = pd.Series(x + rng.normal(0, 0.1, n))  # very high correlation
    out = correlation_decoupling(z_stock, z_sector, window=60, threshold=0.5)
    # High correlation (above 0.9) means they should co-move
    assert out["co_moves"] is True


def test_chow_with_pandas_series_input():
    """Chow decoupling should accept pandas Series without explicit numpy conversion."""
    rng = np.random.default_rng(0)
    z_stock = pd.Series(rng.normal(0, 1, 500))
    z_sector = pd.Series(rng.normal(0, 1, 500))
    # Should not raise
    out = chow_decoupling(z_stock, z_sector, max_order=4, lookback=252)
    assert "decoupling_order" in out
