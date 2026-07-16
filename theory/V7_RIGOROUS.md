# Theory v7 — Rigorous proofs (replaces v1-v6)

**Compiled PDF (9 pages, 261KB):** https://backend.composio.dev/api/v3/sl/UkFPJB4XuQ

## 4 theorems (rigorous proofs)

| Theorem | Statement |
|---------|-----------|
| T1 Variance Contraction | $\V(V^{(k)}) \leq \rho \V(V^{(k-1)}) + O(w^{-2})$, $\V(V^{(k)}) = O(\rho^k)$ |
| T2 Convergence | $\V(V^{(k)}) \to 0$, $V^{(k)} \to \mu$ in $L^2$ |
| T3 Asymptotic Inference | $\bar{\beta}_T \to_p \beta$, $\sqrt{T}(\bar{\beta}_T - \beta) \to_d \N(0, \Omega)$ |
| T4 Affine Invariance | $\tilde{V}^{(k)} = a V^{(k)}$, $\tilde{z}^{(k)} = z^{(k)}$, $\tilde{\beta} = \beta$ |

## Empirical (comprehensive)

| Test | Result |
|------|--------|
| Forecast encompassing (Cascade vs HAR) | $p = 0.0055$ |
| Forecast encompassing (Transformer vs HAR) | $p = 0.47$ |
| Clark-West (Cascade vs HAR) | $p = 0.019$ |
| DM: Combined vs HAR (MSE) | DM $= -9.61$ |
| DM: Combined vs HAR (MAE) | DM $= -18.70$ |
| DM: Combined vs HAR (QLIKE) | DM $= -21.43$ |
| CER improvement | $+0.138$ |
| Sharpe improvement | $+0.77$ |
| Max DD improvement | $+0.116$ |
| Forecast horizon robustness | all $h$ negative |
| Rolling-origin CV | all $-0.21$ to $-0.28$ |

## What v7 fixes (vs v6)

**Mathematical (with reviewer's exact proofs):**
- T1: $O(w^{-2})$ error term, no explicit $\rho$ formula
- T2: does not claim $\mu = 0$
- T3: clean $\alpha$-mixing CLT and HAC consistency
- T4: by induction via positive homogeneity

**Empirical:**
- Forecast horizon robustness
- CER table with Sharpe, Max DD, Turnover
- Ljung-Box: "reduced but remains significant"
- Tables split: predictive accuracy vs DM comparisons
- MCS: "cannot be rejected as inferior"