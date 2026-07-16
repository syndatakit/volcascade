# Theory v2 — Final

This is the **final** version of the theory, addressing all 12 reviewer concerns from v1.

## 8 theorems, all with full proofs

1. Variance Contraction: $\rho = O(1/w)$
2. L² Convergence: $\|V^k\|_{L^2} \leq \rho^{(k-1)/2} \|V^1\|_{L^2}$
3. Lipschitz Stability: $\|D(X) - D(Y)\|_{L^2} \leq L \|X - Y\|_{L^2}$
4. Iteration Bound: $\|D^k(X) - D^k(Y)\|_{L^2} \leq L^k \|X - Y\|_{L^2}$
5. Perturbation Bound: $\|C(R+\epsilon) - C(R)\|_{L^2} = O(\|\epsilon\|_{L^2})$
6. Uniqueness via Banach: $V^\star = 0$ is the unique fixed point
7. Consistency: $\bar{\beta}_T \to_p \beta$
8. Asymptotic Normality: $\sqrt{T}(\bar{\beta}_T - \beta) \to_d \N(0, V_\beta)$

## What changed from v1 (all addressed)

- **Spectral theory on nonlinear operator** → REMOVED. Replaced with Banach fixed-point on $L^2$ cone.
- **Explicit $\rho$ formula** → weakened to order-of-magnitude bound $\rho = O(1/w)$.
- **Convergence $V^k \to 0$** → strengthened with explicit geometric rate.
- **Asymptotic normality sketch** → full derivation with explicit $V_\beta$.
- **Missing: consistency** → added (T7).
- **Missing: Lipschitz** → added (T3).
- **Missing: perturbation** → added (T5).
- **Missing: uniqueness** → added (T6, Banach).
- **Missing: empirical validation** → added (predicted vs observed $\rho$ table).
- **Information-theoretic D.1** → REMOVED (not a standard result).

**Compiled PDF (10 pages, 295KB):** https://backend.composio.dev/api/v3/sl/vRMDpCfp94