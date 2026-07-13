"""Tests for volcascade.cascade — core cascade construction, z-scoring, slope.

These tests use synthetic returns to validate the cascade math. The pilot
on real S&P 500 data is in experiments/pilot_spy.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcascade.cascade import build, entropy, slope, zscore


def test_build_order1_is_realized_vol():
    """Order 1 should be the realized volatility: sqrt(sum of squared returns)."""
    rng = np.random.default_rng(42)
    rets = pd.Series(rng.normal(0, 0.01, size=300))
    cascade = build(rets, orders=(1,), inner_window=20)

    out = cascade[1].dropna()
    # Direct calculation
    expected = rets.pow(2).rolling(20).sum().pow(0.5).dropna()
    pd.testing.assert_series_equal(out, expected, check_names=False)


def test_build_orders_produce_decreasing_warmup():
    """Higher orders should have more NaN warmup rows than lower orders."""
    rng = np.random.default_rng(42)
    rets = pd.Series(rng.normal(0, 0.01, size=500))
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=20)

    nan_counts = {k: c.isna().sum() for k, c in cascade.items()}
    assert nan_counts[1] < nan_counts[2] < nan_counts[3] < nan_counts[4]


def test_build_requires_order_1():
    """build should raise if orders doesn't contain 1."""
    rets = pd.Series(np.random.default_rng(0).normal(0, 0.01, size=100))
    with pytest.raises(ValueError, match="orders must contain 1"):
        build(rets, orders=(2, 3, 4))


def test_zscore_has_unit_variance():
    """After z-scoring, the trailing mean should be ~0 and std ~1 (for stationary series)."""
    rng = np.random.default_rng(42)
    rets = pd.Series(rng.normal(0, 0.01, size=2000))
    cascade = build(rets, orders=(1, 2), inner_window=20)
    z = zscore(cascade, lookback=252)

    z1 = z[1].dropna()
    # Sample mean and std (not the z-score's own mean, but the trailing mean
    # used to construct it should make the z-scored series approximately N(0,1))
    assert abs(z1.mean()) < 0.2
    assert abs(z1.std() - 1.0) < 0.3


def test_slope_is_zero_for_constant_cascade():
    """If all orders have the same z-score, the slope is 0 (flat)."""
    n = 100
    z = {1: pd.Series(np.ones(n)),
         2: pd.Series(np.ones(n)),
         3: pd.Series(np.ones(n)),
         4: pd.Series(np.ones(n))}
    s = slope(z)
    pd.testing.assert_series_equal(s, pd.Series(np.zeros(n)), check_names=False)


def test_slope_positive_when_higher_orders_larger():
    """If z^(4) > z^(3) > z^(2) > z^(1), the slope is positive (steepening)."""
    n = 50
    z = {1: pd.Series(np.linspace(1, 2, n)),
         2: pd.Series(np.linspace(1, 3, n)),
         3: pd.Series(np.linspace(1, 4, n)),
         4: pd.Series(np.linspace(1, 5, n))}
    s = slope(z).dropna()
    # Skip the first row (where all orders are 1, so the cascade is flat by
    # construction). All subsequent rows have z^(4) > z^(3) > z^(2) > z^(1).
    assert (s.iloc[1:] > 0).all()


def test_entropy_max_at_flat_cascade():
    """When all orders have equal |z|, entropy is maximized (= log n_orders)."""
    n = 50
    z = {1: pd.Series(np.ones(n)),
         2: pd.Series(np.ones(n)),
         3: pd.Series(np.ones(n)),
         4: pd.Series(np.ones(n))}
    h = entropy(z)
    assert np.allclose(h, np.log(4))


def test_entropy_low_at_concentrated_cascade():
    """When one order dominates, entropy is low."""
    n = 50
    z = {1: pd.Series(np.zeros(n)),
         2: pd.Series(np.zeros(n)),
         3: pd.Series(np.zeros(n)),
         4: pd.Series(np.ones(n))}
    h = entropy(z)
    assert (h < 0.5).all()  # concentrated on order 4


def test_multivariate_cascade_build():
    """build should work on a DataFrame (multiple assets)."""
    rng = np.random.default_rng(42)
    rets = pd.DataFrame(rng.normal(0, 0.01, size=(300, 3)), columns=["A", "B", "C"])
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=20)
    for k, c in cascade.items():
        assert isinstance(c, pd.DataFrame)
        assert c.shape == rets.shape


def test_adversarial_no_spurious_steepening():
    """Adversarial test: cascade on iid N(0, sigma^2) returns should have slope ~ 0.

    This is the headline robustness check (METHODOLOGY.md Section 9). If
    iid noise produces systematic cascade slope, the cascade is detecting
    artifacts not signal.

    The slope of a 4-point OLS regression on unit-variance z-scores has a
    natural std of ~1/sqrt(5) ~= 0.45 (by construction), so we assert
    std < 1.0 (loose enough to permit natural variation) and mean ~ 0
    (no systematic steepening).
    """
    rng = np.random.default_rng(123)
    n = 5000  # 20 years of daily data
    rets = pd.Series(rng.normal(0, 0.01, size=n))
    cascade = build(rets, orders=(1, 2, 3, 4), inner_window=20)
    z = zscore(cascade, lookback=252)
    s = slope(z).dropna()

    # Mean slope should be close to 0 (no systematic steepening)
    assert abs(s.mean()) < 0.05
    # Std bounded (no runaway cascade)
    assert s.std() < 1.0
