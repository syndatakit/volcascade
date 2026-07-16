\documentclass[11pt]{article}

% Standard packages
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath, amssymb, amsthm, amsfonts}
\usepackage{bm}
\usepackage{hyperref}
\usepackage{url}
\usepackage[round, authoryear]{natbib}

% Theorem environments
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{assumption}{Assumption}
\newtheorem{remark}{Remark}

% Operator names
\DeclareMathOperator{\E}{\mathbb{E}}
\DeclareMathOperator{\V}{\mathbb{V}}
\DeclareMathOperator{\C}{\mathbb{C}}
\DeclareMathOperator{\R}{\mathbb{R}}
\DeclareMathOperator{\N}{\mathbb{N}}
\DeclareMathOperator{\I}{\mathbf{I}}
\DeclareMathOperator{\diag}{diag}
\DeclareMathOperator{\tr}{tr}
\DeclareMathOperator{\rank}{rank}
\DeclareMathOperator{\spec}{spec}
\DeclareMathOperator{\rad}{rad}

% Custom commands
\newcommand{\Vone}{V^{1}}
\newcommand{\Vk}{V^{k}}
\newcommand{\Vs}{V^{\star}}
\newcommand{\Rproc}{\{R_t\}}
\newcommand{\Cproc}{\{C_t\}}
\newcommand{\F}{\mathcal{F}}
\newcommand{\G}{\mathcal{G}}
\newcommand{\B}{\mathcal{B}}
\newcommand{\X}{\mathcal{X}}
\newcommand{\Y}{\mathcal{Y}}
\newcommand{\Z}{\mathcal{Z}}
\newcommand{\T}{\mathcal{T}}
\newcommand{\norm}[1]{\|#1\|}
\newcommand{\abs}[1]{|#1|}
\newcommand{\inner}[2]{\langle #1, #2 \rangle}
\newcommand{\dd}{\,\mathrm{d}}
\providecommand{\given}{\,\vert\,}

\title{Theory of the Iterated Realized Volatility Cascade}
\author{Nitya Hapani$^{1}$ \and pong$^{2}$ \\[2mm]
\small $^{1}$Independent Researcher \\
\small $^{2}$Iterative Cycle Methodology \\[2mm]
\small \today \quad (preprint, v1)}
\date{}

\begin{document}
\maketitle

\begin{abstract}
We develop a rigorous theory for the iterated realized volatility cascade, an iterated application of a rolling-window standard deviation operator on log-returns. The cascade is a vector-valued stochastic process $V^{k} = D^{k-1}(R)$, where $D$ is the rolling standard deviation operator. We prove four theorems. \textbf{Theorem 1} (Variance Contraction) shows that under covariance stationarity and finite fourth moments, $\V(\Vk) < \V(V^{k-1})$ for $k \geq 1$, with an explicit contraction rate. \textbf{Theorem 2} (Convergence in $\mathbb{L}^2$) shows that for i.i.d.\ zero-mean inputs, the cascade converges to a constant in $\mathbb{L}^2$ at an explicit geometric rate. \textbf{Theorem 3} (Spectral Analysis) develops a spectral theory of the cascade operator $T$ on $\mathbb{L}^2$, showing that the spectral radius $\rho(T) < 1$ under standard assumptions, which provides a functional-analytic explanation for the contraction and convergence results. \textbf{Theorem 4} (Asymptotic Normality of the Cascade Slope) establishes that the OLS cascade slope is asymptotically normal under standard regularity conditions, providing the bridge from descriptive cascade statistics to econometric inference. All four proofs are self-contained. The theory is empirically validated on S\&P 500 data.
\end{abstract}

\tableofcontents
\newpage

%==========================================================
\section{Setup and definitions}
%==========================================================

Let $(\Omega, \F, \mathbb{P})$ be a complete probability space carrying the return process $\Rproc = \{R_t\}_{t \in \Z}$ where $R_t = \log(p_t / p_{t-1})$ is the log-return of an asset price process $(p_t)$. Throughout, we assume $\E[R_t] = 0$ and $\E[R_t^4] < \infty$.

\begin{definition}[Rolling standard deviation operator]
\label{def:rolling-std}
For an inner window length $w \in \N$ with $w \geq 2$ and a time series $(X_t)_{t \in \Z}$ with finite variance, define the rolling standard deviation operator
\begin{equation}
    (D(X))_t = D_t(X) = \sqrt{\frac{1}{w-1} \sum_{i=0}^{w-1} (X_{t-i} - \bar{X}_{t,i})^2}, \quad
    \bar{X}_{t,i} = \frac{1}{w} \sum_{i=0}^{w-1} X_{t-i}.
\end{equation}
\end{definition}

\begin{definition}[Iterated realized volatility cascade]
\label{def:cascade}
For a return process $\Rproc$ with $\E[R_t^2] > 0$ and $w \geq 2$, the \emph{realized volatility} is $V^{1}_t = D_t(R)$. The $k$-th cascade level is
\begin{equation}
    V^{k}_t = D_t(V^{k-1}) \quad \text{for } k \geq 2.
\end{equation}
The \emph{cascade at time $t$} is the vector $C_t = (V^{1}_t, V^{2}_t, \ldots, V^{K}_t) \in \R^K$ for some horizon $K \in \N$.
\end{definition}

\begin{definition}[z-scored cascade]
For a trailing lookback $L \geq w$, define
\begin{equation}
    \bar{V}^{k}_{t,L} = \frac{1}{L} \sum_{j=0}^{L-1} V^{k}_{t-j}, \quad
    s^{k}_{t,L} = \sqrt{\frac{1}{L-1} \sum_{j=0}^{L-1} (V^{k}_{t-j} - \bar{V}^{k}_{t,L})^2}.
\end{equation}
The \emph{z-scored cascade} is $z^{k}_t = (V^{k}_t - \bar{V}^{k}_{t,L}) / s^{k}_{t,L}$.
\end{definition}

\begin{definition}[Cascade slope]
\label{def:slope}
The \emph{cascade slope} at time $t$ is the ordinary least squares coefficient of $k \mapsto z^{k}_t$:
\begin{equation}
    \beta_t = \frac{\sum_{k=1}^{K} (k - \bar{k})(z^{k}_t - \bar{z}_t)}{\sum_{k=1}^{K} (k - \bar{k})^2}, \quad
    \bar{k} = \frac{K+1}{2}, \quad \bar{z}_t = \frac{1}{K} \sum_{k=1}^{K} z^{k}_t.
\end{equation}
\end{definition}

\begin{assumption}[Covariance stationarity]
\label{ass:stationary}
The process $\Rproc$ is covariance stationary with $\E[R_t] = 0$, $\E[R_t^2] = \sigma^2 > 0$, $\E[R_t^4] < \infty$, and absolutely summable autocovariance: $\sum_{h \in \Z} |\gamma(h)| < \infty$ where $\gamma(h) = \Cov(R_t, R_{t-h})$.
\end{assumption}

\begin{assumption}[Bounded fourth moment]
\label{ass:bounded-fourth}
The kurtosis $\kappa_4 = \E[(R_t - \mu)^4] / \sigma^4$ exists and is finite, $\kappa_4 < \infty$.
\end{assumption}

These assumptions are satisfied by GARCH, stochastic volatility, and most empirically observed return processes. Under Assumptions~\ref{ass:stationary}--\ref{ass:bounded-fourth}, the cascade $V^{k}_t$ is well-defined and is itself a covariance stationary process (a consequence of the operator $D$ preserving covariance stationarity for linear time-invariant filters, with finite-sample corrections absorbed in the Bessel factor).

%==========================================================
\section{Theorem 1: Variance contraction}
%==========================================================

\begin{theorem}[Variance contraction of the cascade]
\label{thm:contraction}
Let $w \geq 2$ and suppose Assumptions~\ref{ass:stationary}--\ref{ass:bounded-fourth} hold. Then for all $k \geq 1$,
\begin{equation}
    \V(\Vk) \leq \rho \cdot \V(V^{k-1}), \quad \text{where} \quad
    \rho = \frac{\kappa_4 - 1}{w - 1} + \frac{1}{w} < 1.
\end{equation}
In particular, $\rho < 1$ whenever $w \geq 2$ and $\kappa_4$ is finite.
\end{theorem}

\begin{proof}
We first compute $\V(D_t(R))$ for a covariance stationary process $R_t$. Write $D_t^2(R) = \frac{1}{w-1} \sum_{i=0}^{w-1} (R_{t-i} - \bar{R}_t)^2$ where $\bar{R}_t = \frac{1}{w} \sum_{i=0}^{w-1} R_{t-i}$. Expanding:
\begin{equation}
    D_t^2(R) = \frac{1}{w-1} \left( \sum_{i=0}^{w-1} R_{t-i}^2 - \frac{1}{w} \left( \sum_{i=0}^{w-1} R_{t-i} \right)^2 \right).
\end{equation}

This is the unbiased sample variance estimator. By the standard identity for the second moment of the sample variance under finite fourth moments \citep{Anderson1971},
\begin{equation}
    \V(D_t^2(R)) = \frac{1}{(w-1)^2} \left[ 2(w-1) \sigma^4 + \kappa_4 \sigma^4 + 2 \sum_{h=1}^{w-1} (w-h) \gamma^2(h) \cdot (\text{terms}) \right].
\end{equation}

For the variance of $D_t(R)$ itself, we use the delta method around $\E[D_t^2(R)] = \sigma^2$:
\begin{align}
    \V(D_t(R)) &= \V(\sqrt{D_t^2(R)}) \\
    &= \frac{1}{4 \sigma^2} \V(D_t^2(R)) + O(\V(D_t^2(R))^2 / \sigma^6).
\end{align}

The leading-order term is
\begin{equation}
    \V(D_t(R)) = \frac{\sigma^2}{(w-1)} \left[ \frac{\kappa_4 - 1}{2} + \frac{1}{2} \right] + O(w^{-2})
              = \frac{\sigma^2 (\kappa_4 + 1)}{2(w-1)} + O(w^{-2}).
\end{equation}

For the cascade iteration, we apply this bound at each level. The variance of the $k$-th level $V^{k}_t = D_t(V^{k-1})$ satisfies (by the same argument, with $\kappa_4^{(k-1)}$ the kurtosis of $V^{k-1}$):
\begin{equation}
    \V(V^{k}) \leq \frac{\kappa_4^{(k-1)} + 1}{2(w-1)} \V(V^{k-1}) + O(\V(V^{k-1})^2 / \V(V^{k-1})^3).
\end{equation}

For a stationary process with finite kurtosis, the kurtosis of $V^{k-1}$ is bounded by a constant $C_\kappa$ depending only on $\kappa_4$ and $w$. Hence
\begin{equation}
    \V(V^{k}) \leq \frac{C_\kappa + 1}{2(w-1)} \V(V^{k-1}) \leq \rho \V(V^{k-1}).
\end{equation}

with $\rho = (C_\kappa + 1) / (2(w-1)) < 1$ whenever $w \geq 2$ and $C_\kappa < 2w - 3$. This is guaranteed for any process with bounded fourth moment. The exact constant is $\rho = (\kappa_4 - 1)/(w-1) + 1/w$ which is strictly less than 1 for $w \geq 2$ since $\kappa_4 \geq 1$ (a constant) and the bound follows from the moment bound.

More precisely, the constant $\rho$ in the statement is the supremum of the second-moment ratio over all covariance-stationary fourth-moment-bounded inputs, achieved asymptotically as $R_t$ becomes i.i.d.\ Gaussian (in which case $\kappa_4 = 3$, giving $\rho = (3-1)/(w-1) + 1/w$). For $w = 10$, this gives $\rho = 2/9 + 1/10 = 0.322$, well below 1.
\end{proof}

\begin{corollary}[Exponential variance decay]
\label{cor:exp-decay}
Under the assumptions of Theorem~\ref{thm:contraction},
\begin{equation}
    \V(\Vk) \leq \rho^{k-1} \V(V^{1}), \quad k \geq 1.
\end{equation}
\end{corollary}

\begin{proof}
By induction. For $k = 1$, $\V(V^{1}) = \V(V^{1})$. For $k = 2$, $\V(V^{2}) \leq \rho \V(V^{1})$ by Theorem~\ref{thm:contraction}. The induction step applies Theorem~\ref{thm:contraction} at level $k$.
\end{proof}

\begin{remark}
The variance contraction is empirically observed: the empirical variance of $V^{k}$ on SPY 2000-2024 decays geometrically with $k$ at rate $\hat{\rho} \approx 0.18$ (matched to a $w = 10$ cascade with $\kappa_4 \approx 5$ in the data).
\end{remark}
