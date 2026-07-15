"""volcascade: a term structure of differentiation order for realized volatility.

The volatility cascade constructs iterated realized volatilities (order 1
through N), z-scores each order against its trailing history, and summarizes
the joint cross-order behavior as a one-number "cascade slope." The shape
of the cascade (flat vs. steepening vs. inverted) classifies regime breaks
(H1'), marks regime exit (H2 v2), decouples idiosyncratic from systemic
risk in cross-section (H3b), and tests whether these dynamics differ
between developed and frontier markets (H4).

The mathematical treatment and the pre-registered methodology are
documented in docs/DESIGN_MEMO.md (locked design decisions) and the
results/MECHANISM.md writeup (the vol-peak mechanism).
"""

from volcascade.baselines import (
    bai_perron_breaks,
    cusum_regime,
    hmm_regime,
    rcm,
    wasserstein_regime,
)
from volcascade.cascade import build, entropy, slope, zscore
from volcascade.decoupling import (
    chow_decoupling,
    chow_decoupling_cascade,
    chow_statistic,
    correlation_decoupling,
)

__version__ = "0.1.0.dev0"

__all__ = [
    "build",
    "zscore",
    "slope",
    "entropy",
    "chow_decoupling",
    "chow_decoupling_cascade",
    "chow_statistic",
    "correlation_decoupling",
    "bai_perron_breaks",
    "cusum_regime",
    "hmm_regime",
    "rcm",
    "wasserstein_regime",
]
