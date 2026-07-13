"""Tests for volcascade.baselines — comparison battery.

These tests verify the API contracts of the baseline methods. They do
NOT validate the algorithms against ground truth (that requires the
synthetic experiments in the pilot, not unit tests).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcascade.baselines import bai_perron_breaks, cusum_regime, hmm_regime, rcm, wasserstein_regime


def test_hmm_regime_returns_expected_keys():
    """Output should have states, probs, bic, converged."""
    rng = np.random.default_rng(0)
    # Two-regime series: high vol and low vol
    n = 500
    regime = (np.arange(n) > 250).astype(int)
    vol = np.where(regime == 0, 0.01, 0.03)
    series = pd.Series(rng.normal(0, vol))
    out = hmm_regime(series, n_states=2, n_iter=50, random_state=42)

    assert "states" in out
    assert "probs" in out
    assert "bic" in out
    assert "converged" in out
    assert out["states"].shape == (n,)
    assert out["probs"].shape == (n, 2)


def test_hmm_recovers_two_regimes():
    """HMM with n_states=2 should produce different state assignments for high/low vol periods."""
    rng = np.random.default_rng(0)
    n = 500
    regime = (np.arange(n) > 250).astype(int)
    vol = np.where(regime == 0, 0.01, 0.05)
    series = pd.Series(rng.normal(0, vol))
    out = hmm_regime(series, n_states=2, n_iter=100, random_state=42)
    states = out["states"]

    # The HMM should put most of the second half in a different state
    first = states[:250]
    second = states[250:]
    # Modal states should differ
    assert np.bincount(first).argmax() != np.bincount(second).argmax()


def test_wasserstein_regime_returns_labels():
    """Output should have labels of the right shape and centers."""
    rng = np.random.default_rng(0)
    n = 300
    series = pd.Series(np.concatenate([rng.normal(0, 1, n // 2), rng.normal(0, 3, n // 2)]))
    out = wasserstein_regime(series, n_clusters=2, window=60, random_state=42)
    assert "labels" in out
    assert "centers" in out
    assert out["labels"].shape == (n - 60 + 1,)
    assert out["centers"].shape == (2, 5)  # 5-bin histograms, 2 clusters


def test_cusum_returns_expected_keys():
    """Output should have cusum, break_points, critical_value, test_statistic."""
    rng = np.random.default_rng(0)
    series = pd.Series(rng.normal(0, 1, 300))
    out = cusum_regime(series, significance=0.05)
    assert "cusum" in out
    assert "break_points" in out
    assert "critical_value" in out
    assert "test_statistic" in out
    assert isinstance(out["break_points"], list)


def test_cusum_detects_known_break():
    """CUSUM should detect a clear variance break."""
    rng = np.random.default_rng(0)
    n = 500
    # Variance doubles at index 250
    series = pd.Series(np.concatenate([rng.normal(0, 1, 250), rng.normal(0, 3, 250)]))
    out = cusum_regime(series, significance=0.05)
    # Should detect a break (possibly not exactly at 250, but should find one)
    assert len(out["break_points"]) > 0


def test_bai_perron_returns_breaks():
    """Output should have break_points list and optimal_breaks count."""
    rng = np.random.default_rng(0)
    n = 500
    series = pd.Series(np.concatenate([rng.normal(0, 1, 250), rng.normal(0, 3, 250)]))
    out = bai_perron_breaks(series, max_breaks=5)
    assert "break_points" in out
    assert "optimal_breaks" in out
    assert isinstance(out["break_points"], list)
    assert isinstance(out["optimal_breaks"], int)


def test_rcm_bounded():
    """RCM should be bounded between 0 and 100."""
    # Hard states: p=1 or 0, so RCM = 400 * mean(p(1-p)) = 0
    hard_states = np.array([0, 0, 0, 1, 1, 1])
    assert rcm(hard_states) == 0.0

    # Probabilities: p=0.5, so RCM = 400 * 0.5 * 0.5 = 100
    probs = np.array([[0.5, 0.5]] * 10)
    assert abs(rcm(probs) - 100.0) < 1e-6

    # Confident assignments: p=0.9, so RCM = 400 * 0.9 * 0.1 = 36
    probs = np.array([[0.9, 0.1]] * 10)
    assert abs(rcm(probs) - 36.0) < 1e-6


def test_rcm_with_pandas_input():
    """RCM should accept pandas Series as states."""
    states = pd.Series([0, 0, 1, 1, 0, 1])
    val = rcm(states.to_numpy())
    assert val == 0.0  # hard states with p in {0, 1} give RCM = 0
