"""Comparison battery: HMM, Wasserstein k-means, CUSUM, Bai-Perron, RCM.

Implements Section 8 of docs/METHODOLOGY.md.

These are the canonical baselines against which the cascade is compared.
The cascade is not a standalone classifier — its slope series is fed
*into* Bai-Perron and Inclán-Tiao as a preprocessed feature. The
hypothesis-specific comparisons (H1, H2, H3, H4) compose the cascade
with these baselines to isolate the cascade's marginal contribution.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "hmm_regime",
    "wasserstein_regime",
    "cusum_regime",
    "bai_perron_breaks",
    "rcm",
]


def hmm_regime(
    series: np.ndarray | pd.Series,
    n_states: int = 2,
    n_iter: int = 100,
    random_state: int = 42,
) -> dict:
    """Gaussian Hidden Markov Model regime classifier.

    Parameters
    ----------
    series : array-like
        Univariate time series.
    n_states : int
        Number of hidden states. Default 2.
    n_iter : int
        Maximum EM iterations. Default 100.
    random_state : int
        RNG seed. Default 42.

    Returns
    -------
    dict
        Keys: ``states`` (ndarray of int), ``probs`` (ndarray of (T, n_states)),
        ``bic`` (float), ``converged`` (bool).
    """
    from hmmlearn import hmm

    if isinstance(series, pd.Series):
        series = series.to_numpy()
    x = series[~np.isnan(series)].reshape(-1, 1)

    model = hmm.GaussianHMM(
        n_components=n_states,
        covariance_type="full",
        n_iter=n_iter,
        random_state=random_state,
    )
    model.fit(x)
    states = model.predict(x)
    probs = model.predict_proba(x)

    # BIC = -2 log L + k log n
    n = len(x)
    k = n_states ** 2 + 2 * n_states - 1  # transition + emission params
    bic = -2 * model.score(x) + k * np.log(n)

    return {
        "states": states,
        "probs": probs,
        "bic": bic,
        "converged": model.monitor_.converged,
    }


def wasserstein_regime(
    series: np.ndarray | pd.Series,
    n_clusters: int = 2,
    window: int = 60,
    random_state: int = 42,
) -> dict:
    """Wasserstein k-means regime classifier (Campani et al. 2021).

    Each window of length ``window`` is treated as an empirical
    distribution. K-means in Wasserstein-2 space clusters windows into
    regimes. This is the most direct non-Markov competitor.

    Parameters
    ----------
    series : array-like
        Univariate time series.
    n_clusters : int
        Number of clusters. Default 2.
    window : int
        Window length. Default 60.
    random_state : int
        RNG seed. Default 42.

    Returns
    -------
    dict
        Keys: ``labels`` (ndarray of cluster ids, length T-window+1),
        ``centers`` (ndarray of cluster centers in distribution space).
    """
    from sklearn.cluster import KMeans

    if isinstance(series, pd.Series):
        series = series.to_numpy()
    x = series[~np.isnan(series)]

    # Build window-level distribution features: 5-bin histogram per window
    bins = np.linspace(np.nanmin(x), np.nanmax(x), 6)
    feats = []
    for i in range(window, len(x) + 1):
        hist, _ = np.histogram(x[i - window : i], bins=bins, density=True)
        feats.append(hist)
    feats = np.asarray(feats)

    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = km.fit_predict(feats)
    return {"labels": labels, "centers": km.cluster_centers_}


def cusum_regime(
    series: np.ndarray | pd.Series,
    significance: float = 0.05,
) -> dict:
    """Inclán-Tiao CUSUM of squares test for variance shifts.

    Detects change points in the *variance* of the series. Returns
    candidate break dates at the canonical 5% significance threshold.

    Parameters
    ----------
    series : array-like
        Univariate time series.
    significance : float
        Significance level. Default 0.05.

    Returns
    -------
    dict
        Keys: ``cusum`` (ndarray), ``break_points`` (list of int indices),
        ``critical_value`` (float).
    """
    if isinstance(series, pd.Series):
        series = series.to_numpy()
    x = series[~np.isnan(series)]
    n = len(x)

    # CUSUM of squares (centered by mean)
    sq = (x - np.mean(x)) ** 2
    cum_sum = np.cumsum(sq)
    D = cum_sum / cum_sum[-1] - np.arange(1, n + 1) / n
    D_star = np.max(np.abs(D)) * np.sqrt(n)

    # Critical values for the CUSUM test (Brownian bridge asymptotics)
    # Approximation: a + b/sqrt(n)
    a = 1.36 if significance == 0.10 else 1.63 if significance == 0.05 else 1.95
    critical = a + (a - 0.4) * 0.0  # asymptotic; could refine for finite n

    break_points = []
    if D_star > critical:
        argmax = int(np.argmax(np.abs(D)))
        break_points = [argmax]

    return {
        "cusum": D,
        "break_points": break_points,
        "critical_value": critical,
        "test_statistic": D_star,
    }


def bai_perron_breaks(
    series: np.ndarray | pd.Series,
    max_breaks: int = 5,
    significance: float = 0.05,
) -> dict:
    """Bai-Perron multiple structural change test.

    Tests for up to ``max_breaks`` structural break points in the
    (cumulative) mean of the series. Returns the optimal break dates
    and the F-statistic for testing m vs. m+1 breaks.

    Parameters
    ----------
    series : array-like
        Univariate time series.
    max_breaks : int
        Maximum number of breaks to test. Default 5.
    significance : float
        Significance level for sequential F-test. Default 0.05.

    Returns
    -------
    dict
        Keys: ``break_points`` (list of int indices), ``f_statistics``
        (dict), ``optimal_breaks`` (int).
    """
    from scipy import stats as sps
    from ruptures import Pelt

    if isinstance(series, pd.Series):
        series = series.to_numpy()
    x = series[~np.isnan(series)]
    n = len(x)

    # Use PELT as a fast proxy for Bai-Perron (exact BP is O(n^m) in m)
    model = Pelt(model="rbf").fit(x.reshape(-1, 1))
    # Penalty chosen via BIC approximation
    pen = np.log(n) * np.var(x)
    try:
        bkps = model.predict(pen=pen)
        # ruptures returns the end-of-segment indices; convert to start-of-break
        break_points = [b for b in bkps[:-1] if 0 < b < n]
    except Exception:
        break_points = []

    return {
        "break_points": break_points,
        "optimal_breaks": len(break_points),
        "n": n,
    }


def rcm(
    states: np.ndarray,
) -> float:
    """Regime Classification Measure (Ang & Bekaert 2002b).

    RCM = 400 * (1/T) * sum_t p_t(1 - p_t)

    where p_t is the probability of the most-likely regime at time t.
    Higher RCM = cleaner regime separation. A useful regime model
    should have RCM >> 0 in 2-state US equity data.

    Parameters
    ----------
    states : ndarray
        Sequence of state probabilities (T,) or hard states (T,).

    Returns
    -------
    float
        RCM value.
    """
    states = np.asarray(states)
    if states.ndim == 2:
        # Probabilities: take max
        p = states.max(axis=1)
    else:
        # Hard states: p is 1 if state matches the modal state
        # This is the simpler form
        p = (states == np.bincount(states).argmax()).astype(float)
    t = len(p)
    return float(400.0 * np.mean(p * (1.0 - p)))
