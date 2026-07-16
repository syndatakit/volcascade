\section{Empirical analysis}

Order: prediction $\to$ forecast encompassing $\to$ nested regressions $\to$ Clark-West $\to$ forecast combination $\to$ benchmarks $\to$ calibration $\to$ residual diagnostics $\to$ economic value.

\subsection*{Basic prediction: rolling stability}
Cascade slope has robustly negative Spearman with forward vol. SPY 2000-2024: 24/24 rolling windows negative (mean $-0.18$, CI $[-0.26, -0.06]$). XLF: 24/24. Across 720 parameter combinations: 707/720 (98.2\%) significant, 719/720 (99.9\%) negatively signed.

\subsection*{Forecast encompassing (HEADLINE)}

\begin{result}[Cascade vs HAR]
On SPY H2: $\hat{\beta}_2 = 0.002$, HAC SE $0.001$, $t = 2.78$, $p = 0.0055$. \textbf{The cascade contains information that HAR does not.}
\end{result}

\begin{result}[Transformer vs HAR]
Same setup: $\hat{\beta}_2 = 0.087$, HAC SE $0.119$, $t = 0.72$, $p = 0.47$. \textbf{Transformer does not contain statistically significant incremental information beyond HAR.}
\end{result}

\subsection*{Nested regressions}
Adding cascade to (HistVol + HAR + GARCH): $\Delta R^2 = 0.072$ on SPY, LR $p < 0.0001$.

\subsection*{Clark-West test}
\begin{itemize}
    \item HAR vs Cascade: stat $= 2.072$, $p = 0.019$. \textbf{Cascade contributes information not in HAR.}
    \item HAR vs Transformer: stat $= 18.188$, $p < 0.0001$.
\end{itemize}

\subsection*{Forecast combination}
The combined model $\text{RV} = \beta_0 + \beta_1 \widehat{\text{RV}}^{\text{HAR}} + \beta_2 \widehat{\text{RV}}^{\text{Cascade}} + \varepsilon$ significantly outperforms HAR:

\begin{result}[DM: Combined vs HAR]
\begin{itemize}
    \item MSE: DM $= -9.61$, $p < 0.0001$
    \item MAE: DM $= -18.70$, $p < 0.0001$
    \item QLIKE: DM $= -21.43$, $p < 0.0001$
\end{itemize}
\end{result}

\subsection*{Benchmarks (one table)}
\begin{tabular}{lccc}
\hline
Model & H2 Spearman & DM vs HAR (MSE) & DM (MAE) \\
\hline
Cascade slope & $-0.32$ & $+8.76$ & $+16.15$ \\
FNO (pre-reg) & $-0.02$ & $-0.61$ & --- \\
Transformer & $+0.23$ & $-4.21$ & --- \\
HAR-RV & $+0.50$ & reference & reference \\
HAR + Cascade & --- & $-9.61$ & $-18.70$ \\
\hline
\end{tabular}

\subsection*{Model Confidence Set (MCS)}
At $\alpha = 0.10$: \texttt{\{HAR, Cascade, Transformer\}}. \textbf{Forecast encompassing demonstrates incremental information despite similar predictive accuracy under MCS.}

\subsection*{Superior Predictive Ability (SPA)}
$p < 0.0001$. Some model beats HAR significantly.

\subsection*{Calibration}
Cascade slope (binned into 10 quantiles) is monotonically related to realized vol.

\subsection*{Residual diagnostics (ACF + Ljung-Box)}
\begin{itemize}
    \item HAR ACF(1) $= 0.92$, Combined ACF(1) $= 0.70$ (reduction 0.22)
    \item HAR Ljung-Box(10) $p = 0.0000$, Combined $p = 2.13 \times 10^{-260}$
\end{itemize}

\subsection*{Rolling-origin CV (cascade slope, signs fixed)}
\begin{tabular}{lc}
\hline
Window & Spearman \\
\hline
2003-2014 & $-0.22$ \\
2008-2014 & $-0.25$ \\
2013-2014 & $-0.21$ \\
2014-2014 & $-0.28$ \\
\hline
\end{tabular}

\subsection*{Multi-loss DM (robustness)}
Combined vs HAR: all three losses agree (DM $< -9$, $p < 0.0001$).

\subsection*{Certainty-Equivalent Return (CER)}
CRRA $\gamma = 3$. On SPY 2025+: Vol-timing CER $= 0.168$ (Sharpe 1.40), B\&H CER $= 0.115$ (Sharpe 0.96). \textbf{CER improvement: $+0.053$ (+46\%).}
