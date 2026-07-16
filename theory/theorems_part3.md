\section{Discussion: contribution}

\textbf{Why higher-order volatility geometry exists.} Volatility is multi-scale. At the daily scale, realized vol $V^1$ captures recent fluctuations. At weekly/monthly scales, the rolling std of $V^1$ captures higher-order clustering. The cascade slope summarizes all four scales into a single number. Empirically, this summary is robustly negative on SPY (24/24), XLF (24/24), and 99.9\% across 720 parameter combinations.

\textbf{Why HAR misses it.} HAR models persistence in volatility magnitude (yesterday's vol, weekly avg, monthly avg). The cascade captures geometric shape of vol across scales. These are different aspects. The forecast-encompassing test confirms: cascade contributes information not in HAR ($p = 0.0055$). The combined model (HAR + Cascade) significantly outperforms HAR on MSE, MAE, QLIKE.

\textbf{Why multi-scale operators matter.} The cascade is an iterated application of a single operator (rolling std). The operator $D$ is nonlinear (sample std, not a linear filter), so the cascade is a nonlinear multi-scale operator. Theorem 1 (variance contraction) shows the cascade is well-behaved. Theorem 2 (L$^2$ convergence) shows it converges to a constant. Theorem 4 (z-score invariance) makes the cascade slope scale-invariant.

\textbf{Why the contribution is the cascade, not the neural network.} The Transformer has better squared error in isolation, but the encompassing test shows the Transformer does not contribute information beyond HAR ($p = 0.47$). The cascade contributes information beyond HAR ($p = 0.0055$). The contribution is the cascade as a new volatility statistic, not a new neural network.

\section*{Summary}
\begin{tabular}{lc}
\hline
Test & Result \\
\hline
Forecast encompassing (Cascade vs HAR) & $p = 0.0055$ \\
Forecast encompassing (Transformer vs HAR) & $p = 0.47$ \\
Clark-West (Cascade vs HAR) & $p = 0.019$ \\
Nested $\Delta R^2$ & $0.072$ \\
DM: Combined vs HAR (MSE) & DM $= -9.61$ \\
DM: Combined vs HAR (MAE) & DM $= -18.70$ \\
DM: Combined vs HAR (QLIKE) & DM $= -21.43$ \\
SPA & $p < 0.0001$ \\
MCS & \{HAR, Cascade, Transformer\} \\
CER improvement & $+0.053$ (+46\%) \\
Rolling-origin CV & all negative, mean $-0.24$ \\
\hline
\end{tabular}

\section*{What v6 changes (vs v5)}
Removed non-rigorous theorems. Forecast encompassing as headline. Compressed Transformer. Fixed rolling-origin CV signs. CER leads. Ljung-Box added. Forecast combination. Multi-loss DM. Discussion: 10\% FNO, 90\% contribution.

\section*{Acknowledgments}
We thank the anonymous reviewers for their detailed feedback.

\section*{Appendix: Notation}
\begin{itemize}
    \item $\Rproc = \{R_t\}$: log-return process
    \item $D$: rolling std operator
    \item $V^{k}_t = D_t^{k-1}(R_t)$: cascade level
    \item $z^{k}_t$: z-scored $V^{k}_t$
    \item $C_t$: cascade
    \item $\beta_t$: cascade slope
    \item $\rho$: variance contraction constant
\end{itemize}

\begin{thebibliography}{9}
\bibitem[Anderson(1971)]{Anderson1971}
Anderson, T. W. (1971). \emph{The Statistical Analysis of Time Series}. John Wiley \& Sons.

\bibitem[Andrews(1991)]{Andrews1991}
Andrews, D. W. K. (1991). HAC covariance matrix estimation. \emph{Econometrica}, 59(3), 817--858.

\bibitem[Clark and West(2007)]{ClarkWest2007}
Clark, T. E., and West, K. D. (2007). \emph{Journal of Econometrics}, 138(1), 291--311.

\bibitem[Doukhan(1994)]{Doukhan1994}
Doukhan, P. (1994). \emph{Mixing: Properties and Examples}. Springer.

\bibitem[Hansen, Lunde, and Nason(2011)]{HansenLundeNason2011}
Hansen, P. R., Lunde, A., and Nason, J. M. (2011). The model confidence set. \emph{Econometrica}, 79(2), 453--497.

\bibitem[White(2000)]{White2000}
White, H. (2000). A reality check for data snooping. \emph{Econometrica}, 68(5), 1097--1126.

\bibitem[Billingsley(1995)]{Billingsley1995}
Billingsley, P. (1995). \emph{Probability and Measure}. John Wiley \& Sons.

\bibitem[Hamilton(1994)]{Hamilton1994}
Hamilton, J. D. (1994). \emph{Time Series Analysis}. Princeton University Press.

\bibitem[Ljung and Box(1978)]{LjungBox1978}
Ljung, G. M., and Box, G. E. P. (1978). \emph{Biometrika}, 65(2), 297--303.

\end{thebibliography}

\end{document}
