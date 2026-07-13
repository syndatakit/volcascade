"""volcascade: a term structure of differentiation order for realized volatility.

The volatility cascade constructs iterated realized volatilities (order 1
through N), z-scores each order against its trailing history, and summarizes
the joint cross-order behavior as a one-number "cascade slope." The shape
of the cascade (flat vs. steepening vs. inverted) classifies regime breaks
(H1), marks regime exit (H2), decouples idiosyncratic from systemic risk
in cross-section (H3), and tests whether these dynamics differ between
developed and frontier markets (H4).

See docs/METHODOLOGY.md for the full mathematical treatment.
"""

from volcascade.cascade import build, entropy, slope, zscore
from volcascade.decoupling import chow_decoupling, correlation_decoupling
from volcascade.baselines import hmm_regime, wasserstein_regime, cusum_regime

__version__ = "0.1.0.dev0"

__all__ = [
    "build",
    "zscore",
    "slope",
    "entropy",
    "chow_decoupling",
    "correlation_decoupling",
    "hmm_regime",
    "wasserstein_regime",
    "cusum_regime",
]
