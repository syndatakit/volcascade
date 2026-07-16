%==========================================================
\section{Empirical analysis: forecast encompassing and related tests}
%==========================================================

The empirical analysis is centered on a single question: \textbf{does the cascade contain information that classical HAR does not?}

\subsection{Forecast encompassing (HEADLINE)}

The forecast-encompassing test regresses realized vol on a baseline plus a new predictor. Significantly positive $\hat{\beta}_2$ means the new predictor contains information not in the baseline.

\begin{result}[Cascade vs HAR]
On SPY H2 (2010-2014): $\hat{\beta}_2 = 0.002$, HAC SE $0.001$, $t = 2.78$, $p = 0.0055$. \textbf{The cascade contains information that HAR does not.}
\end{result}

\begin{result}[Transformer vs HAR]
Same setup with Transformer: $\hat{\beta}_2 = 0.087$, HAC SE $0.119$, $t = 0.72$, $p = 0.4691$. \textbf{The Transformer does not contain statistically significant incremental information beyond HAR.}
\end{result}

\begin{result}[Nested regression]
Adding the cascade to (HistVol + HAR + GARCH): $\Delta R^2 = 0.072$ on SPY, LR test $p < 0.0001$.
\end{result}

\subsection{Clark-West test}

The Clark-West test is designed for nested forecasting models.

\begin{result}[Clark-West]
On SPY H2:
\begin{itemize}
    \item HAR vs Cascade: Clark-West stat $= 2.072$, $p = 0.019$. \textbf{Cascade contains information not in HAR.}
    \item HAR vs Transformer: Clark-West stat $= 18.188$, $p < 0.0001$. \textbf{Transformer contains information not in HAR.}
\end{itemize}
\end{result}

\subsection{Model Confidence Set (MCS)}

The Model Confidence Set (Hansen, Lunde, Nason 2011) identifies which models are statistically indistinguishable at a given confidence level.

\begin{result}[MCS at $\alpha = 0.10$]
On SPY H2, the MCS contains: \texttt{\{HAR, Cascade, Transformer\}}. These three models are statistically indistinguishable from each other on squared-error loss.
\end{result}

\subsection{Superior Predictive Ability (SPA)}

White's SPA test tests the null that no model in a collection is significantly better than a benchmark.

\begin{result}[SPA]
On SPY H2, SPA $p$-value $= 0.000$. \textbf{Some model in the collection significantly outperforms HAR.}
\end{result}

\subsection{Certainty Equivalent Return (CER)}

CRRA utility with $\gamma = 3$: $\text{CER} = \bar{r} - (\gamma/2) \cdot \V(r)$. The vol-timing strategy yields:

\begin{result}[CER comparison]
On SPY 2025+:
\begin{itemize}
    \item Vol-timing: CER $= 0.143$, Sharpe $= 1.18$
    \item Buy-hold: CER $= 0.115$, Sharpe $= 0.96$
    \item CER improvement: $+0.028$
\end{itemize}
\end{result}

\subsection{Rolling-origin cross-validation}

Four rolling-origin windows:

\begin{table}[h]
\centering
\begin{tabular}{lc}
\hline
Train start -- Test end & Spearman \\
\hline
2003-01-01 -- 2014-12-31 & $+0.23$ \\
2008-01-01 -- 2014-12-31 & $+0.30$ \\
2013-01-01 -- 2014-12-31 & $+0.22$ \\
2014-01-01 -- 2014-12-31 & $+0.39$ \\
\hline
\end{tabular}
\end{table}

\subsection{Calibration}

The cascade prediction, binned into 10 quantiles, is monotonically related to realized vol.

\subsection{Residual diagnostics}

\begin{result}[Residual ACF]
\begin{itemize}
    \item HAR residual ACF(1) $= 0.92$
    \item HAR + Cascade residual ACF(1) $= 0.70$
    \item Reduction: $0.22$
\end{itemize}
\end{result}

%==========================================================
\section{Summary of empirical validation}
%==========================================================

\begin{table}[h]
\centering
\begin{tabular}{lc}
\hline
Test & Result \\
\hline
Forecast encompassing (Cascade vs HAR) & $p = 0.0055$ \\
Forecast encompassing (Transformer vs HAR) & $p = 0.47$ (not significant) \\
Clark-West (Cascade vs HAR) & $p = 0.019$ \\
Clark-West (Transformer vs HAR) & $p < 0.0001$ \\
SPA (some model beats HAR) & $p < 0.0001$ \\
MCS at $\alpha = 0.10$ & \{HAR, Cascade, Transformer\} \\
Nested regression $\Delta R^2$ (Cascade) & $0.072$, $p < 0.0001$ \\
CER improvement (vol-timing) & $+0.028$ \\
Rolling-origin CV (4 windows) & all positive, mean $+0.29$ \\
Calibration & monotonic \\
Residual ACF reduction & $0.22$ \\
\hline
\end{tabular}
\end{table}
