\section{Data}

We use daily adjusted close prices from Yahoo Finance for two universes:

\textbf{US assets (5):} SPY, XLK, XLF, XLV, XLE. Sample period 2000-01-01 to 2026-07-15.

\textbf{International assets (5):} EWJ, EFA, GLD, TSM, ASHR. Sample period 2004-01-01 to 2026-07-15.

Log returns are $R_t = \log(p_t / p_{t-1})$. Forward realized volatility is the square root of the sum of squared returns over a window of length $h$ (forecast horizon), shifted forward by $h$ days.

The cascade is constructed with inner window $w = 10$, z-score lookback $L = 120$, and $K = 4$ levels. The forecast horizon is $h = 5$ days. We test robustness to $h \in \{1, 2, 3, 5, 10, 20\}$.

\section{Empirical results}

\subsection{Basic prediction: rolling stability}

Cascade slope Spearman with forward 5-day vol in 3-year rolling windows 2002--2024:

\begin{tabular}{lcc}
\hline
Asset & Windows with $\rho < 0$ & Mean $\rho$ \\
\hline
SPY & 24 / 24 & $-0.18$ \\
XLF & 24 / 24 & $-0.16$ \\
\hline
\end{tabular}

\subsection{Parameter sweep}

720 parameter combinations on SPY 2000--2024 (varying $w, L, h, K$). 707/720 (98.2\%) statistically significant. 719/720 (99.9\%) negatively signed.

\subsection{Pre-registered architecture selection}

8 architectures tested. Transformer selected (validation Spearman $0.240$).

\subsection{Forecast encompassing (HEADLINE)}

\begin{result}[Cascade vs HAR]
On SPY H2: $\hat{\beta}_2 = 0.002$, HAC SE $0.001$, $t = 2.78$, $p = 0.0055$. \textbf{Cascade contains information that HAR does not.}
\end{result}

\begin{result}[Transformer vs HAR]
$\hat{\beta}_2 = 0.087$, HAC SE $0.119$, $t = 0.72$, $p = 0.47$. \textbf{Transformer does not contain statistically significant incremental information beyond HAR.}
\end{result}

\subsection{Nested regressions}

Adding cascade to (HistVol + HAR + GARCH): $\Delta R^2 = 0.072$, LR $p < 0.0001$ on SPY. All 5 US assets significant.

\subsection{Clark--West test}

\begin{itemize}
    \item HAR vs Cascade: stat $= 2.072$, $p = 0.019$.
    \item HAR vs Transformer: stat $= 18.188$, $p < 0.0001$.
\end{itemize}

\subsection{Forecast horizon robustness}

$\rho(h)$ for $h \in \{1, 2, 3, 5, 10, 20\}$: all negative ($-0.111$ to $-0.173$).

\subsection{Forecast combination}

Combined (HAR + Cascade) vs HAR: DM $-9.61$ (MSE), $-18.70$ (MAE), $-21.43$ (QLIKE), all $p < 0.0001$.

\subsection{Pre-registered benchmark comparison}

11 models on SPY. Cascade is the only one with negative Spearman on both holdouts. Combined HAR + Cascade beats HAR on three losses.

\subsection{Model Confidence Set}

MCS at $\alpha = 0.10$: $\{$HAR, Cascade, Transformer$\}$. Cannot be rejected as inferior.

\subsection{Superior Predictive Ability}

SPA $p = 0.000$. Some model beats HAR significantly.

\subsection{Calibration}

Cascade slope (binned into 10 quantiles) is monotonically related to realized vol.

\subsection{Residual diagnostics}

HAR ACF(1) $= 0.92$, Combined ACF(1) $= 0.70$. Ljung-Box p-value: HAR $\approx 0$, Combined $2.13 \times 10^{-260}$. Reduced but remains statistically significant.

\subsection{Walk-forward CV}

Cascade slope is negative on all 4 windows ($-0.22$ to $-0.28$).

\subsection{International evidence}

Per-region Transformer has 5/5 negative H1 Spearman on intl. Limited transferability.

\subsection{Economic value: CER}

On SPY 2025+:

\begin{tabular}{lcccc}
\hline
Strategy & Sharpe & Max DD & Turnover & CER \\
\hline
Vol-timing & 1.86 & $-0.072$ & 0.12 & 0.284 \\
B\&H & 1.09 & $-0.188$ & 0.00 & 0.146 \\
\hline
\end{tabular}
\end{document}
