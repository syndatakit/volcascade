\section{Empirical analysis}

Order: prediction $\to$ forecast encompassing $\to$ nested regressions $\to$ Clark-West $\to$ forecast combination $\to$ benchmarks $\to$ calibration $\to$ residual diagnostics $\to$ economic value.

\subsection*{Basic prediction: rolling stability}
Cascade slope has robustly negative Spearman with forward vol. SPY 2000-2024: 24/24 rolling windows negative (mean $-0.18$, 95\% CI $[-0.26, -0.06]$). XLF: 24/24. Across 720 parameter combinations: 707/720 (98.2\%) significant, 719/720 (99.9\%) negatively signed.

\subsection*{Forecast encompassing (HEADLINE)}

\begin{result}[Cascade vs HAR]
On SPY H2: $\hat{\beta}_2 = 0.002$, HAC SE $0.001$, $t = 2.78$, $p = 0.0055$. \textbf{The cascade contains information that HAR does not.}
\end{result}

\begin{result}[Transformer vs HAR]
$\hat{\beta}_2 = 0.087$, HAC SE $0.119$, $t = 0.72$, $p = 0.47$. \textbf{Transformer does not contain statistically significant incremental information beyond HAR.}
\end{result}

\subsection*{Nested regressions}
Adding cascade to (HistVol + HAR + GARCH): $\Delta R^2 = 0.072$ on SPY, LR $p < 0.0001$.

\subsection*{Clark-West test}
\begin{itemize}
    \item HAR vs Cascade: stat $= 2.072$, $p = 0.019$.
    \item HAR vs Transformer: stat $= 18.188$, $p < 0.0001$.
\end{itemize}

\subsection*{Forecast horizon robustness}
The cascade slope's Spearman with forward vol, computed for forecast horizons $h \in \{1, 2, 3, 5, 10, 20\}$ days:

\begin{tabular}{cc}
\hline
$h$ (days) & Spearman \\
\hline
1 & $-0.111$ \\
2 & $-0.153$ \\
3 & $-0.164$ \\
5 & $-0.173$ \\
10 & $-0.167$ \\
20 & $-0.159$ \\
\hline
\end{tabular}

\textbf{Result is negative for all forecast horizons.} Mean Spearman: $-0.155$.

\subsection*{Forecast combination}
The combined model $\text{RV}_{t+5} = \beta_0 + \beta_1 \widehat{\text{RV}}^{\text{HAR}}_t + \beta_2 \widehat{\text{RV}}^{\text{Cascade}}_t + \varepsilon_{t+1}$ significantly outperforms HAR:

\begin{result}[DM: Combined vs HAR]
\begin{itemize}
    \item MSE: DM $= -9.61$, $p < 0.0001$
    \item MAE: DM $= -18.70$, $p < 0.0001$
    \item QLIKE: DM $= -21.43$, $p < 0.0001$
\end{itemize}
\end{result}

\subsection*{Benchmarks (one table)}

\begin{table}[h]
\centering
\caption{Table 1: Predictive accuracy (SPY H2)}
\begin{tabular}{lcc}
\hline
Model & H2 Spearman & Squared-error loss \\
\hline
HAR-RV & $+0.50$ & reference \\
Cascade slope & $-0.32$ & worse (different target) \\
Transformer & $+0.23$ & better than HAR \\
FNO (pre-reg) & $-0.02$ & statistically tied \\
GARCH(1,1) & $+0.47$ & similar to HAR \\
HAR + Cascade & --- & better than HAR \\
\hline
\end{tabular}
\end{table}

\begin{table}[h]
\centering
\caption{Table 2: Diebold-Mariano comparisons (SPY H2)}
\begin{tabular}{lcccc}
\hline
Comparison & DM & $p$ & Loss & Winner \\
\hline
HAR vs Cascade & $+8.76$ & $< 0.001$ & MSE & HAR \\
HAR vs Transformer & $-4.21$ & $< 0.001$ & MSE & Transformer \\
HAR vs GARCH & $-1.20$ & $0.23$ & MSE & tied \\
HAR vs FNO & $-0.61$ & $0.54$ & MSE & tied \\
HAR + Cascade vs HAR & $-9.61$ & $< 0.001$ & MSE & Combined \\
HAR + Cascade vs HAR & $-18.70$ & $< 0.001$ & MAE & Combined \\
HAR + Cascade vs HAR & $-21.43$ & $< 0.001$ & QLIKE & Combined \\
\hline
\end{tabular}
\end{table}

\subsection*{Model Confidence Set (MCS)}
At $\alpha = 0.10$: \texttt{\{HAR, Cascade, Transformer\}}. \textbf{These models cannot be rejected as inferior to the best-performing model.}

\subsection*{Superior Predictive Ability (SPA)}
$p < 0.0001$.

\subsection*{Calibration}
Cascade slope, binned into 10 quantiles, is monotonically related to realized vol.

\subsection*{Residual diagnostics (ACF + Ljung-Box)}
Adding cascade to HAR reduces residual autocorrelation:
\begin{itemize}
    \item HAR ACF(1) $= 0.92$, Combined ACF(1) $= 0.70$ (reduction 0.22)
    \item HAR Ljung-Box(10) $p = 0.0000$
    \item Combined Ljung-Box(10) $p = 2.13 \times 10^{-260}$
\end{itemize}

\textbf{Residual autocorrelation is reduced but remains statistically significant.} The cascade captures some but not all of the volatility structure that HAR misses.

\subsection*{Multi-loss DM (robustness)}
Combined model wins on all three loss functions (MSE, MAE, QLIKE).

\subsection*{Certainty-Equivalent Return (CER) and economic value}
CRRA utility with $\gamma = 3$. On SPY 2025+:

\begin{table}[h]
\centering
\begin{tabular}{lcccc}
\hline
Strategy & Sharpe & Max DD & Turnover & CER \\
\hline
Vol-timing & 1.86 & $-0.072$ & 0.12 & 0.284 \\
Buy-and-hold & 1.09 & $-0.188$ & 0.00 & 0.146 \\
\hline
Improvement & $+0.77$ & $+0.116$ & --- & $+0.138$ \\
\hline
\end{tabular}
\end{table}

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
