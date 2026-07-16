# Theory v6 — Minimal + comprehensive empirical

**Compiled PDF (9 pages, 259KB):** https://backend.composio.dev/api/v3/sl/1yDtRLXG9H

## 4 theorems (only)

| Theorem | Statement |
|---------|-----------|
| T1 Variance Contraction | $\exists \rho \in (0,1)$: $\V(V^k) \leq \rho \V(V^{k-1})$ under $\kappa_4 < w-1+1/w$ |
| T2 L² Convergence | $\|V^k\|_{L^2} \leq \rho^{(k-1)/2} \|V^1\|_{L^2}$ |
| T3 Asymptotic Inference | $\bar{\beta}_T \to_p \beta$, $\sqrt{T}(\bar{\beta}_T - \beta) \to_d \N(0, V_\beta)$ |
| T4 Z-score Invariance | Cascade slope invariant to affine rescaling |

## Comprehensive empirical (forecast encompassing is headline)

| Test | Result |
|------|--------|
| Forecast encompassing (Cascade vs HAR) | $p = 0.0055$ |
| Forecast encompassing (Transformer vs HAR) | $p = 0.47$ |
| Clark-West (Cascade vs HAR) | $p = 0.019$ |
| Nested $\Delta R^2$ | $0.072$, $p < 0.0001$ |
| DM: Combined vs HAR (MSE) | DM $= -9.61$ |
| DM: Combined vs HAR (MAE) | DM $= -18.70$ |
| DM: Combined vs HAR (QLIKE) | DM $= -21.43$ |
| SPA | $p < 0.0001$ |
| MCS | {HAR, Cascade, Transformer} |
| CER improvement | $+0.053$ (+46\%) |
| Rolling-origin CV (cascade slope) | all negative, mean $-0.24$ |
| Ljung-Box p-value (HAR) | $0.0000$ |
| Ljung-Box p-value (Combined) | $2.13 \times 10^{-260}$ |

## Tier corrections applied

**Tier 1:** Removed non-rigorous theorems, forecast encompassing as headline, compressed Transformer, MCS honest.

**Tier 2:** Fixed rolling-origin CV signs, CER leads, Ljung-Box added, forecast combination, DM Cascade+HAR vs HAR, discussion 10% FNO, multi-loss DM.

## The story

The cascade contributes information not contained in HAR. The combined model (HAR + Cascade) significantly outperforms HAR on all three loss functions. The cascade is the contribution.