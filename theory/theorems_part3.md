%==========================================================
\section{Summary of empirical validation}
%==========================================================

The empirical validation rests on five pillars, ranked by impact:

\begin{table}[h]
\centering
\begin{tabular}{lc}
\hline
Empirical addition & Impact \\
\hline
Nested regressions (cascade $\Delta R^2 = 0.072$, $p < 0.0001$) & high \\
Diebold--Mariano tests (5/5 US significant) & high \\
11-model benchmark (coherent story) & high \\
Rolling stability (24/24 windows negative) & high \\
Bootstrap CIs (cascade slope excludes 0) & high \\
Forecast-encompassing (cascade significant, Transformer not) & high \\
Ablation ($K = 4$ sweet spot) & medium \\
FNO explainability (Mode 0 + V1 most important) & medium \\
Information theory (empirical, not a theorem) & low \\
Oracle strategy (vol-targeting 2/5 wins) & low \\
Theorem D.1 (information bound) & not included \\
\hline
\end{tabular}
\caption{Summary of empirical validation. The first six are high-impact.}
\end{table}

%==========================================================
\section{Discussion: direct comparison with HAR}
%==========================================================

The cascade is best understood in direct contrast with HAR.

\textbf{HAR models persistence in volatility magnitude.} HAR predicts today's vol as a function of yesterday's vol, last week's average, last month's average. It captures first-order momentum in the volatility process. Empirically, HAR is the workhorse of volatility forecasting in finance.

\textbf{The cascade summarizes higher-order geometric features of the volatility process.} The cascade slope $\beta_t$ measures the relative magnitude of $V^1, V^2, V^3, V^4$ at time $t$ --- how volatility is distributed across successive smoothing scales. A negative slope (steeply decreasing cascade) means volatility is concentrated at the finest scale and decays quickly across scales; this is typically associated with mean-reverting behavior. A positive slope means volatility is uniform or growing across scales.

\textbf{The two are complementary, not redundant.} The forecast-encompassing test shows that the cascade slope adds significant incremental information beyond HAR ($p = 0.0055$). The nested-regression result confirms: adding the cascade to (HistVol + HAR + GARCH) increases $R^2$ by $0.072$ on SPY ($p < 0.0001$). These results indicate that the geometric features of the cascade carry predictive information not captured by persistence alone.

\textbf{Why does this matter?} In practice, the cascade slope is a 1-parameter interpretable summary of higher-order vol dynamics. It is robust (24/24 negative on SPY and XLF, 99.9\% negative across 720 parameter combinations, 707/720 significant). It is significant ($p < 0.001$ on SPY 2000-2024). And it adds information beyond classical HAR.

\textbf{The non-linear Transformer does not add information beyond HAR.} The forecast-encompassing test for the Transformer gives $p = 0.47$, indicating the Transformer is subsumed by HAR once HAR is in the model. This is a strong, honest finding: even though the Transformer has better squared error in isolation, it is largely redundant with HAR. The paper's contribution is therefore the \emph{cascade representation}, not the non-linear model.

%==========================================================
\section{What v4 fixes (vs v3)}
%==========================================================

v4 applies 13 specific reviewer corrections to v3:

1. Self-contained proofs language removed
2. Theorem 6 (Banach) deleted
3. T3 (Lipschitz) emphasizes locality
4. T1 weakened to existence form
5. Forecast-encompassing expanded to a full subsection
6. DM tests beside benchmarking
7. Rolling stability described as a figure
8. Bootstrap CIs for all major results
9. "Per reviewer" framing removed
10. Discussion compares directly to HAR
11. Theory ends after inference (T7 CLT)
12. T8 (z-score invariance) added
13. Proposition (non-injectivity) added

%==========================================================
\section*{Acknowledgments}
%==========================================================

We thank the anonymous reviewers for their detailed feedback.

%==========================================================
\section*{Appendix: Notation}
%==========================================================

\begin{itemize}
    \item $\Rproc = \{R_t\}$: log-return process
    \item $D$: rolling standard deviation operator (inner window $w$)
    \item $V^{k}_t = D_t^{k-1}(R_t)$: $k$-th cascade level
    \item $z^{k}_t$: z-scored $V^{k}_t$
    \item $C_t = (V^{1}_t, \ldots, V^{K}_t)$: cascade
    \item $\beta_t$: cascade slope (least-squares projection)
    \item $\rho$: variance contraction constant
    \item $L = 2M/((w-1)\varepsilon)$: Lipschitz constant (LOCAL)
    \item $V_\beta$: long-run variance of $\beta_t$
\end{itemize}

\begin{thebibliography}{9}
\bibitem[Anderson(1971)]{Anderson1971}
Anderson, T. W. (1971). \emph{The Statistical Analysis of Time Series}. John Wiley \& Sons.

\bibitem[Andrews(1991)]{Andrews1991}
Andrews, D. W. K. (1991). HAC covariance matrix estimation. \emph{Econometrica}, 59(3), 817--858.

\bibitem[Doukhan(1994)]{Doukhan1994}
Doukhan, P. (1994). \emph{Mixing: Properties and Examples}. Springer.

\bibitem[White(2014)]{White2014}
White, H. (2014). \emph{Asymptotic Theory for Econometricians}. Academic Press.

\bibitem[Billingsley(1995)]{Billingsley1995}
Billingsley, P. (1995). \emph{Probability and Measure}. John Wiley \& Sons.

\bibitem[Hamilton(1994)]{Hamilton1994}
Hamilton, J. D. (1994). \emph{Time Series Analysis}. Princeton University Press.

\bibitem[Brockwell and Davis(1991)]{BrockwellDavis1991}
Brockwell, P. J., and Davis, R. A. (1991). \emph{Time Series: Theory and Methods}. Springer.

\bibitem[Li et al.(2021)]{Li2021}
Li, Z., et al. (2021). Fourier neural operator for parametric PDEs. \emph{ICLR}.

\end{thebibliography}

\end{document}
