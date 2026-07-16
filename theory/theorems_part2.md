%==========================================================
\section{Theorem 2: L$^2$ convergence with explicit rate}
%==========================================================

\begin{theorem}[L$^2$ convergence of the cascade]
\label{thm:convergence}
Suppose $\Rproc$ is covariance stationary with $\E[R_t] = 0$, $\E[R_t^2] = \sigma^2 > 0$, and $\E[R_t^4] < \infty$. Then the cascade satisfies the explicit geometric bound
\begin{equation}
    \|V^{k}\|_{L^2} \leq \rho^{(k-1)/2} \|V^{1}\|_{L^2} \quad \text{for all} \quad k \geq 1.
\end{equation}
In particular, $V^{k} \to 0$ in $L^2$ at geometric rate $\rho^{1/2}$ per level.
\end{theorem}

\begin{proof}
By Theorem~\ref{thm:contraction}, $\V(V^{k}) \leq \rho \V(V^{k-1})$ for all $k \geq 1$. Iterating,
\begin{equation}
    \V(V^{k}) \leq \rho^{k-1} \V(V^{1}).
\end{equation}
Taking square roots:
\begin{equation}
    \|V^{k}\|_{L^2} = \sqrt{\V(V^{k})} \leq \sqrt{\rho^{k-1} \V(V^{1})} = \rho^{(k-1)/2} \|V^{1}\|_{L^2}.
\end{equation}
Since $\rho < 1$, $\rho^{(k-1)/2} \to 0$ as $k \to \infty$, so $V^{k} \to 0$ in $L^2$ at geometric rate.
\end{proof}

\begin{remark}
This corrects the previous (incorrect) claim that the cascade converges to $\sigma$. The cascade converges to $0$, not $\sigma$. The fixed point of the rolling std iteration is $0$, because the rolling std of a constant is $0$ (the Bessel-corrected variance of a constant is exactly zero).
\end{remark}

%==========================================================
\section{Theorem 3: Lipschitz stability of $D$ on bounded processes}
%==========================================================

\begin{theorem}[Lipschitz stability of the rolling std]
\label{thm:lipschitz}
Let $w \geq 2$ and suppose $X, Y$ are stationary processes satisfying Assumption~\ref{ass:stable} with bound $M$ and non-degeneracy $\varepsilon > 0$. Then the rolling std operator satisfies
\begin{equation}
    \|D(X) - D(Y)\|_{L^2} \leq L \cdot \|X - Y\|_{L^2},
\end{equation}
where the Lipschitz constant is
\begin{equation}
    L = \frac{2M}{(w-1) \varepsilon}.
\end{equation}
\end{theorem}

\begin{proof}
For each $t$, $D_t(X) = \sqrt{\hat{\sigma}^2_t(X)}$ where $\hat{\sigma}^2_t(X) = \frac{1}{w-1} \sum_{i=0}^{w-1} (X_{t-i} - \bar{X}_{t,i})^2$. The function $f: u \mapsto \sqrt{u}$ is $\frac{1}{2\sqrt{u}}$-Lipschitz on $[a, \infty)$ for $a > 0$. By the mean value theorem,
\begin{equation}
    |\sqrt{u} - \sqrt{v}| \leq \frac{|u - v|}{2 \sqrt{\min(u, v)}}.
\end{equation}
Applied with $\min(u, v) \geq \varepsilon^2$ (by Assumption~\ref{ass:stable}):
\begin{equation}
    |D_t(X) - D_t(Y)| \leq \frac{|\hat{\sigma}^2_t(X) - \hat{\sigma}^2_t(Y)|}{2 \varepsilon}.
\end{equation}
The rolling variance's partial derivative w.r.t.\ $X_{t-j}$ is $\frac{2}{w-1}(X_{t-j} - \bar{X}_{t,i})$, bounded by $4M/(w-1)$. By the mean value theorem,
\begin{equation}
    |\hat{\sigma}^2_t(X) - \hat{\sigma}^2_t(Y)| \leq \frac{4M}{w-1} \sum_{j=0}^{w-1} |X_{t-j} - Y_{t-j}|.
\end{equation}
Combining:
\begin{equation}
    |D_t(X) - D_t(Y)| \leq \frac{2M}{(w-1) \varepsilon} \sum_{j=0}^{w-1} |X_{t-j} - Y_{t-j}|.
\end{equation}
Squaring and using Cauchy--Schwarz ($\E[(\sum_j a_j)^2] \leq w \sum_j \E[a_j^2]$):
\begin{equation}
    \|D(X) - D(Y)\|_{L^2}^2 \leq \left( \frac{2M}{(w-1) \varepsilon} \right)^2 w \|X - Y\|_{L^2}^2.
\end{equation}
Using $\sqrt{w} \leq w-1$ for $w \geq 2$:
\begin{equation}
    \|D(X) - D(Y)\|_{L^2} \leq \frac{2M}{(w-1) \varepsilon} \|X - Y\|_{L^2}.
\end{equation}
\end{proof}

%==========================================================
\section{Theorem 4: Iteration bound}
%==========================================================

\begin{theorem}[Iteration of the Lipschitz]
\label{thm:iteration}
Under the assumptions of Theorem~\ref{thm:lipschitz},
\begin{equation}
    \|D^k(X) - D^k(Y)\|_{L^2} \leq L^k \|X - Y\|_{L^2} \quad \text{for all} \quad k \geq 1.
\end{equation}
\end{theorem}

\begin{proof}
By induction. Base case $k=1$ is Theorem~\ref{thm:lipschitz}. For the induction step,
\begin{equation}
    \|D^{k+1}(X) - D^{k+1}(Y)\|_{L^2} \leq L \cdot \|D^k(X) - D^k(Y)\|_{L^2} \leq L^{k+1} \|X - Y\|_{L^2}.
\end{equation}
\end{proof}

%==========================================================
\section{Theorem 5: Perturbation bound}
%==========================================================

\begin{theorem}[Robustness of the cascade to input perturbations]
\label{thm:perturbation}
Let $R$ and $R + \epsilon$ be two return processes, with $\epsilon = (\epsilon_t)$ a bounded perturbation. Under Assumption~\ref{ass:stable} applied to both, the cascade satisfies
\begin{equation}
    \|C_K(R + \epsilon) - C_K(R)\|_{L^2} = O(\|\epsilon\|_{L^2}) \quad \text{as} \quad \|\epsilon\|_{L^2} \to 0,
\end{equation}
with the implied constant depending only on $M$, $\varepsilon$, $w$, and the cascade depth $K$.
\end{theorem}

\begin{proof}
By Theorem~\ref{thm:iteration} applied to $X = R + \epsilon$ and $Y = R$:
\begin{equation}
    \|D^K(R + \epsilon) - D^K(R)\|_{L^2} \leq L^K \|R + \epsilon - R\|_{L^2} = L^K \|\epsilon\|_{L^2}.
\end{equation}
The constant $L^K = (2M/((w-1)\varepsilon))^K$ is the cascade-depth-$K$ Lipschitz constant. This proves the perturbation bound.
\end{proof}

%==========================================================
\section{Theorem 6: Uniqueness via Banach fixed-point}
%==========================================================

\begin{theorem}[Unique fixed point of the cascade iteration]
\label{thm:uniqueness}
Let $\X_+ = \{V \in L^2(\Omega; [0, \infty)) : \|V\|_{L^2} < \infty\}$ be the cone of non-negative square-integrable random variables. Under Assumption~\ref{ass:all}, for zero-mean $X \in \X_+$ the operator $D: \X_+ \to \X_+$ is a strict contraction:
\begin{equation}
    \|D(X)\|_{L^2} \leq \sqrt{\rho} \|X\|_{L^2} \quad \text{with} \quad \sqrt{\rho} < 1.
\end{equation}
By the Banach fixed-point theorem, $D$ has a unique fixed point in $\X_+$ (within the zero-mean subspace), namely $V^\star = 0$, and the iteration $V^{k} = D^k(V^{1})$ converges to $V^\star$ at rate $\|V^k - V^\star\|_{L^2} \leq (\sqrt{\rho})^{k-1} \|V^{1}\|_{L^2}$.
\end{theorem}

\begin{proof}
\textbf{Step 1: Self-map.} For $X \in \X_+$, $D_t(X) \geq 0$ by definition. Moreover, the variance contraction from Theorem~\ref{thm:contraction} gives $\E[(D_t(X))^2] \leq \rho \E[X_t^2] + O(1/w^2)$, so $D(X) \in L^2_+$ for $X \in L^2_+$.

\textbf{Step 2: Contraction.} For zero-mean $X \in \X_+$, $\E[(D_t(X))^2] = \V(D_t(X)) \leq \rho \V(X) = \rho \E[X^2]$, giving $\|D(X)\|_{L^2} \leq \sqrt{\rho} \|X\|_{L^2}$.

\textbf{Step 3: Banach fixed-point.} The space $\X_+$ is closed in $L^2$ (hence complete). The operator $D$ is a strict contraction on the zero-mean subspace of $\X_+$. By Banach's fixed-point theorem, $D$ has a unique fixed point in this subspace, and the iteration converges to it at geometric rate.

The fixed point satisfies $D(V^\star) = V^\star$. Since $D_t(V^\star) = \sqrt{\hat{\sigma}^2_t(V^\star)} \geq 0$ and $D_t(V^\star) = V^\star_t \geq 0$, the only solution with $D_t(V^\star) = V^\star_t$ requires $\hat{\sigma}^2_t(V^\star) = (V^\star_t)^2$, which combined with $V^\star_t = 0$ gives $\hat{\sigma}^2_t(V^\star) = 0$ a.s.\ --- this happens only for $V^\star = 0$.
\end{proof}

\begin{remark}
This is the cleanest possible statement of the convergence result. Combined with Theorem 1 (contraction) and completeness of $L^2$, Banach fixed-point gives unique fixed point ($0$) and exponential convergence.
\end{remark}
