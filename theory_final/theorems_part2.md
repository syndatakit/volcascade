\section{Empirical analysis}

Order: prediction $\to$ forecast encompassing $\to$ nested regressions $\to$ Clark-West $\to$ forecast combination $\to$ benchmarks $\to$ calibration $\to$ residual diagnostics $\to$ economic value.

\subsection*{Basic prediction: rolling stability}
Cascade slope has robustly negative Spearman with forward vol. SPY 2000-2024: 24/24 rolling windows negative. XLF: 24/24. Across 720 parameter combinations: 707/720 (98.2\%) significant, 719/720 (99.9\%) negatively signed.

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
$\rho(h)$ for $h \in \{1, 2, 3, 5, 10, 20\}$ days: $-0.111$, $-0.153$, $-0.164$, $-0.173$, $-0.167$, $-0.159$. \textbf{Result is negative for all forecast horizons.}

\subsection*{Forecast combination}
Combined model $\text{RV}_{t+5} = \beta_0 + \beta_1 \widehat{\text{RV}}^{\text{HAR}} + \beta_2 \widehat{\text{RV}}^{\text{Cascade}} + \varepsilon$ significantly outperforms HAR:
\begin{itemize}
    \item MSE: DM $= -9.61$, $p < 0.0001$
    \item MAE: DM $= -18.70$, $p < 0.0001$
    \item QLIKE: DM $= -21.43$, $p < 0.0001$
\end{itemize}

\subsection*{Benchmarks (one table)}
\begin{tabular}{lcc}
\hline
Model & H2 Spearman & DM vs HAR (MSE) \\
\hline
HAR-RV & $+0.50$ & reference \\
Cascade slope & $-0.32$ & $+8.76$ \\
Transformer & $+0.23$ & $-4.21$ \\
HAR + Cascade & --- & $-9.61$ \\
\hline
\end{tabular}

\subsection*{Model Confidence Set (MCS)}
At $\alpha = 0.10$: \texttt{\{HAR, Cascade, Transformer\}}. \textbf{These models cannot be rejected as inferior.}

\subsection*{Residual diagnostics (ACF + Ljung-Box)}
\begin{itemize}
    \item HAR ACF(1) $= 0.92$, Combined ACF(1) $= 0.70$ (reduction 0.22)
    \item HAR Ljung-Box(10) $p = 0.0000$, Combined $p = 2.13 \times 10^{-260}$
\end{itemize}
\textbf{Residual autocorrelation is reduced but remains statistically significant.}

\subsection*{Certainty-Equivalent Return (CER)}
CRRA utility with $\gamma = 3$. On SPY 2025+:

\begin{tabular}{lcccc}
\hline
Strategy & Sharpe & Max DD & Turnover & CER \\
\hline
Vol-timing & 1.86 & $-0.072$ & 0.12 & 0.284 \\
Buy-and-hold & 1.09 & $-0.188$ & 0.00 & 0.146 \\
\hline
\end{tabular}
\end{document>
