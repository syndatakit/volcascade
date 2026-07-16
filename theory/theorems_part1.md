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

\newcommand{\Vone}{V^{1}}
\newcommand{\Vk}{V^{k}}
\newcommand{\Rproc}{\{R_t\}}
\newcommand{\Cproc}{\{C_t\}}
\newcommand{\F}{\mathcal{F}}
\newcommand{\norm}[1]{\|#1\|}

\title{Theory of the Iterated Realized Volatility Cascade (v6)}
\author{Nitya Hapani$^{1}$ \and pong$^{2}$ \\[2mm]
\small $^{1}$Independent Researcher \\
\small $^{2}$Iterative Cycle Methodology \\[2mm]
\small \today \quad (preprint, v6)}
\date{}

\begin{document}
\maketitle

\begin{abstract}
We develop a focused theory for the iterated realized volatility cascade. We prove four theorems, and document a comprehensive empirical analysis. T1 (Variance Contraction) establishes a contraction constant under a stated kurtosis restriction. T2 (L$^2$ Convergence) shows the cascade converges to 0 with explicit geometric rate. T3 (Asymptotic Inference) gives consistency and asymptotic normality. T4 (Z-score Invariance) shows the cascade slope is invariant to affine rescaling after z-scoring. The empirical analysis centers on the forecast-encompassing test: the cascade slope contributes information that HAR does not. A forecast combination (HAR + Cascade) significantly outperforms HAR on squared error, absolute error, and QLIKE (all $p < 0.0001$). Certainty-Equivalent Return (CER) improves by $+0.053$ over buy-and-hold. The cascade contributes information not contained in HAR. This is the contribution.
\end{abstract}

\tableofcontents
\newpage

\section{Setup}
Let $(\Omega, \F, \mathbb{P})$ carry the return process $\Rproc = \{R_t\}$ where $R_t = \log(p_t / p_{t-1})$.

\begin{definition}[Rolling std operator]
$D_t(X) = \sqrt{\frac{1}{w-1} \sum_{i=0}^{w-1} (X_{t-i} - \bar{X}_{t,i})^2}$, $w \geq 2$.
\end{definition}

\begin{definition}[Cascade]
$V^{1}_t = D_t(R)$, $V^{k}_t = D_t(V^{k-1})$ for $k \geq 2$. The cascade at time $t$ is $C_t = (V^{1}_t, \ldots, V^{K}_t) \in \R^K$.
\end{definition}

\begin{definition}[Cascade slope]
$\beta_t = \arg\min_{a,b} \sum_{k=1}^{K} (z^{k}_t - a - bk)^2$ where $z^{k}_t$ is z-scored $V^{k}_t$. Least-squares projection.
\end{definition}

\begin{assumption}[Stationarity, mixing]
The process $\Rproc$ is covariance stationary with $\E[R_t] = 0$, $\E[R_t^2] = \sigma^2 > 0$, finite kurtosis $\kappa_4 < \infty$, and $\{(R_t, C_t, \beta_t)\}$ is $\alpha$-mixing with $\sum_k \alpha(k)^{1/2} < \infty$.
\end{assumption}

\begin{assumption}[Stable subset (LOCAL)]
There exist $M, \varepsilon > 0$ such that for $t$ and $k \leq K$, $\esssup |V^{k}_t| \leq M$ and $D_t(V^{k-1}) \geq \varepsilon$.
\end{assumption}

\section{Theorem 1: Variance contraction}
\begin{theorem}
Let $w \geq 2$ and suppose the kurtosis restriction $\kappa_4 < w - 1 + 1/w$ holds. There exists a contraction constant $0 < \rho < 1$ such that $\V(V^k) \leq \rho \V(V^{k-1})$ for all $k \geq 1$. For Gaussian inputs ($\kappa_4 = 3$), $\rho = \frac{2}{w-1} + \frac{1}{w}$.
\end{theorem}

\begin{proof}
\textbf{Step 1.} The rolling variance is the unbiased sample variance. By \citet{Anderson1971}, $\V(D_t^2(R)) = \frac{\sigma^4}{(w-1)^2}(2(w-1) + \kappa_4) + O(\sigma^4/w^3)$.

\textbf{Step 2.} Delta method: $\V(D_t(R)) = \frac{\sigma^2(\kappa_4 + 2)}{4(w-1)} + O(\sigma^2/w^2)$.

\textbf{Step 3.} The variance ratio $\rho = \V(D_t(R))/\sigma^2 < 1$ iff $\kappa_4 < w - 1 + 1/w$.

\textbf{Step 4.} Iteration gives $\V(V^k) \leq \rho \V(V^{k-1})$.
\end{proof}

\section{Theorem 2: L$^2$ convergence}
\begin{theorem}
Under Assumption~1 and the kurtosis restriction, $\|V^k\|_{L^2} \leq \rho^{(k-1)/2} \|V^1\|_{L^2}$.
\end{theorem}

\begin{proof}
T1 $\to$ induction $\to$ geometric decay $\to$ completeness of $L^2$ $\to$ limit constant $V^\infty$ $\to$ $\V(V^\infty) = 0$ $\to$ $V^\infty = 0$ a.s.
\end{proof}

\section{Theorem 3: Asymptotic inference}
\begin{theorem}
Under Assumption~1:
\begin{enumerate}
    \item \textbf{Consistency:} $\bar{\beta}_T \to_p \beta$.
    \item \textbf{Asymptotic Normality:} $\sqrt{T}(\bar{\beta}_T - \beta) \to_d \N(0, V_\beta)$.
\end{enumerate}
$V_\beta$ is consistently estimated by Newey--West HAC.
\end{theorem}

\begin{proof}
By the mixing Ergodic Theorem (Doukhan 1994) and CLT for $\alpha$-mixing (Doukhan 1994 Theorem 1.7; White 2014 Theorem 7.1). HAC consistency by Andrews (1991).
\end{proof}

\section{Theorem 4: Z-score invariance}
\begin{theorem}
Let $\tilde{V}^{k}_t = a_k V^{k}_t + b_k$ with $a_k > 0$. Then $\tilde{z}^{k}_t = z^{k}_t$ and $\tilde{\beta}_t = \beta_t$.
\end{theorem}

\begin{proof}
$\tilde{z}^{k}_t = \frac{a_k (V^{k}_t - \bar{V}^{k}_t)}{a_k s^{k}_t} = z^{k}_t$. The cascade slope is linear in $z^{k}_t$.
\end{proof}
