# Theory v5 — Minimal + comprehensive empirical

**Compiled PDF (10 pages, 269KB):** https://backend.composio.dev/api/v3/sl/KQn5tsQEuX

This is v5 of the theory. It applies Tier 1-4 corrections from the reviewer.

## 4 theorems + 4 propositions (minimal)

| Theorems (kept) | Propositions (demoted) |
|----------------|-------------------------|
| T1: Variance Contraction | P1: Lipschitz stability (LOCAL) |
| T2: L² Convergence | P2: Iteration |
| T3: Asymptotic Inference | P3: Perturbation |
| T4: Z-score Invariance | P4: Non-injectivity |

## Comprehensive empirical

| Test | Result |
|------|--------|
| Forecast encompassing (Cascade vs HAR) | $p = 0.0055$ |
| Forecast encompassing (Transformer vs HAR) | $p = 0.47$ (not significant) |
| Clark-West (Cascade vs HAR) | $p = 0.019$ |
| Clark-West (Transformer vs HAR) | $p < 0.0001$ |
| SPA | $p < 0.0001$ |
| MCS at $\alpha = 0.10$ | {HAR, Cascade, Transformer} |
| Nested $\Delta R^2$ | $0.072$, $p < 0.0001$ |
| CER improvement | $+0.028$ |
| Rolling-origin CV (4 windows) | all positive, mean $+0.29$ |
| Calibration | monotonic |
| Residual ACF reduction | $0.22$ |

## Tier corrections applied

**Tier 1 (must fix):** Stop overselling theory, remove theorems for elegance, forecast-encompassing as headline, replace "best" with "incremental".

**Tier 2:** Clark-West, MCS, R² decomposition.

**Tier 3:** CER, SPA, rolling-origin CV.

**Tier 4:** Calibration, residual diagnostics.

**Removed:** Spectral theorem (already removed), information bound, oracle strategy, "seven theorems" framing.

## The story

**The cascade contributes information not contained in HAR.** Forecast encompassing, Clark-West, nested regression, residual ACF, and rolling-origin CV all confirm. The Transformer has better squared error in isolation but is subsumed by HAR in the encompassing test. The cascade is the contribution.

## How to compile

```bash
cd theory
python3 build_theorems.py
pdflatex theorems.tex
```