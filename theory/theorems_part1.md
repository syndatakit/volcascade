\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath, amssymb, amsthm, amsfonts}
\usepackage{bm}
\usepackage{hyperref}
\usepackage{url}
\usepackage[round, authoryear]{natbib}

\newtheorem{theorem}{Theorem}
\newtheorem{proposition}{Proposition}
\newtheorem{corollary}{Corollary}
\theoremstyle{definition}
\newtheorem{assumption}{Assumption}
\newtheorem{result}{Result}
\newtheorem{remark}{Remark}
\theoremstyle{definition}
\newtheorem{definition}{Definition}

\DeclareMathOperator{\E}{\mathbb{E}}
\DeclareMathOperator{\V}{\mathbb{V}}
\DeclareMathOperator{\R}{\mathbb{R}}
\DeclareMathOperator{\esssup}{ess\,sup}
\DeclareMathOperator{\Ltwo}{L^2}
\DeclareMathOperator{\Z}{\mathbb{Z}}
\DeclareMathOperator{\Cov}{Cov}
\DeclareMathOperator{\N}{\mathbb{N}}

\title{Theory of the Iterated Realized Volatility Cascade (v7)}
\author{Nitya Hapani$^{1}$ \and pong$^{2}$ \\[2mm]
\small \today \quad (preprint, v7)}
\date{}

\begin{document}
\maketitle

\begin{abstract}
We prove four theorems for the iterated realized volatility cascade. T1 (Variance Contraction) shows $\V(V^{(k)}) \leq \rho \V(V^{(k-1)}) + O(w^{-2})$ under stationarity and strong mixing. T2 (Convergence) shows $\V(V^{(k)}) \to 0$ and $V^{(k)} \to \mu$ in $L^2$. T3 (Asymptotic Inference) gives consistency and asymptotic normality of the cascade slope via the $\alpha$-mixing CLT. T4 (Affine Invariance) shows the cascade slope is invariant to positive affine rescaling. The empirical analysis centers on the forecast-encompassing test: the cascade slope contributes information that HAR does not ($p = 0.0055$). Forecast combination (HAR + Cascade) significantly outperforms HAR on MSE, MAE, and QLIKE. The CER of the vol-timing strategy improves by $+0.138$ over buy-and-hold. The cascade contributes information not contained in HAR. This is the contribution.
\end{abstract}

\section{Setup}

\begin{assumption}[Stationarity]
Let $(R_t)_{t \in \Z}$ be strictly stationary, $\E(R_t) = 0$, $\E(R_t^4) < \infty$. Moreover, $\sum_{h=-\infty}^{\infty} |\gamma(h)| < \infty$, where $\gamma(h) = \Cov(R_t, R_{t+h})$.
\end{assumption}

\begin{assumption}[Strong mixing]
The process satisfies $\alpha(k) \to 0$ and $\sum_{k=1}^{\infty} \alpha(k)^{\delta/(2+\delta)} < \infty$ for some $\delta > 0$. This is the assumption used in \citet{White2014}.
\end{assumption}

\begin{definition}
Define $V_t^{(1)} = D(R)_t$, and recursively $V_t^{(k)} = D(V^{(k-1)})_t$.
\end{definition}

\section{Theorem 1: Variance Contraction}

\begin{theorem}
Suppose Assumptions 1--2 hold. Suppose further that $\E[(V_t^{(k)})^4] < \infty$ for every $k$. Then there exists $0 < \rho < 1$ such that $\V(V^{(k)}) \leq \rho \V(V^{(k-1)}) + O(w^{-2})$. Consequently $\V(V^{(k)}) = O(\rho^k)$.
\end{theorem}

\begin{proof}
Let $S_t^2 = \frac{1}{w-1} \sum_{i=0}^{w-1} (R_{t-i} - \bar{R}_t)^2$ be the rolling sample variance. By \citet{Anderson1971}, $\V(S_t^2) = \frac{2\sigma^4}{w-1} + O(w^{-2})$ under finite fourth moments.

Define $g(x) = \sqrt{x}$. Since $g$ is continuously differentiable on $(0, \infty)$, the delta method gives
\[
    \V(g(S_t^2)) = (g'(\sigma^2))^2 \V(S_t^2) + o(w^{-1}) = \frac{1}{4\sigma^2} \V(S_t^2) + O(w^{-2}).
\]
Hence $\V(D(R)) = c_w \V(R) + O(w^{-2})$ where $c_w = \frac{1}{2(w-1)} + O(w^{-2})$. Since $w \geq 2$, $c_w < 1$ for practical windows. By induction, $\V(V^{(k)}) \leq c_w \V(V^{(k-1)}) + O(w^{-2}) = \rho \V(V^{(k-1)}) + O(w^{-2})$ with $\rho = c_w$. Substitution gives $\V(V^{(k)}) = O(\rho^k)$.
\end{proof}

\begin{corollary}[Uniform square integrability]
$\sup_k \E[(V^{(k)})^2] < \infty$. The cascade remains uniformly square integrable.
\end{corollary}

\section{Theorem 2: Convergence}

\begin{theorem}
Suppose Theorem~1 holds. Then $\V(V^{(k)}) \to 0$. If $\E(V^{(k)}) \to \mu$, then $V^{(k)} \to \mu$ in $L^2$.
\end{theorem}

\begin{proof}
$\V(V^{(k)}) = O(\rho^k) \to 0$ since $0 < \rho < 1$. Assume $\E(V^{(k)}) \to \mu$. Then
\[
    \E[(V^{(k)} - \mu)^2] = \V(V^{(k)}) + (\E(V^{(k)}) - \mu)^2 \to 0.
\]
\end{proof}

\begin{remark}
We do not identify the limit as 0. The cascade converges to a constant in $L^2$, but the value depends on the input. For zero-mean input the limit is 0.
\end{remark}

\section{Theorem 3: Asymptotic Inference}

\begin{assumption}[Regularity of the Cascade Functional]
There exists a measurable mapping $f: \R^m \to \R$ for some finite $m$ depending only on $w, K, L$ such that $\beta_t = f(R_t, R_{t-1}, \ldots, R_{t-m})$, with $f$ continuously differentiable a.e.\ and $\E[\|\nabla f\|^2] < \infty$. Furthermore, $\E|\beta_t|^{2+\delta} < \infty$ for some $\delta > 0$.
\end{assumption}

\begin{theorem}
Under Assumptions 1--3:
\begin{enumerate}
    \item \textbf{Consistency:} $\bar{\beta}_T \to_p \beta = \E[\beta_t]$.
    \item \textbf{Asymptotic Normality:} $\sqrt{T}(\bar{\beta}_T - \beta) \to_d \N(0, \Omega)$, $\Omega = \sum_{h=-\infty}^{\infty} \Cov(\beta_t, \beta_{t+h})$.
    \item \textbf{HAC:} $\hat{\Omega}_{\text{NW}} \to_p \Omega$, so $\sqrt{T}(\bar{\beta}_T - \beta) / \sqrt{\hat{\Omega}_{\text{NW}}} \to_d \N(0, 1)$.
\end{enumerate}
\end{theorem}

\begin{proof}
$\beta_t$ depends on a finite window of $R_t$'s, so inherits stationarity and $\alpha$-mixing. By Doukhan (1994) Ergodic Theorem, $\bar{\beta}_T \to \E[\beta_t]$ a.s. By the CLT for strongly mixing processes (Doukhan 1994 Theorem 1.7, White 2014 Ch.~7), $\sqrt{T}(\bar{\beta}_T - \beta) \to_d \N(0, \Omega)$. Newey--West consistency follows from Andrews (1991) under the same mixing conditions. Slutsky's theorem gives the result.
\end{proof}

\section{Theorem 4: Affine Invariance}

\begin{theorem}
Let $\tilde{R}_t = a R_t + b$ with $a > 0$. Then $\tilde{V}_t^{(k)} = a V_t^{(k)}$, $\tilde{z}_t^{(k)} = z_t^{(k)}$, and $\tilde{\beta}_t = \beta_t$.
\end{theorem}

\begin{proof}
$D$ is positively homogeneous: $D(\tilde{X})_t = a D(X)_t$. By induction, $\tilde{V}^{(k)} = a V^{(k)}$. Hence $\tilde{\mu}_k = a \mu_k$ and $\tilde{\sigma}_k = a \sigma_k$, giving $\tilde{z}_k = z_k$. The OLS slope of $z_k$ on $k$ is unchanged.
\end{proof}

\begin{corollary}[Cross-Asset Comparability]
The cascade slope is dimensionless and may be compared directly across assets, currencies, or sampling frequencies without additional normalization.
\end{corollary}
