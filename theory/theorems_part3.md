\section{Discussion: contribution}

\textbf{Why higher-order volatility geometry exists.} The cascade applies the rolling standard deviation operator iteratively, producing a progressively smoother representation of realized volatility. Each level captures the volatility distribution at a coarser time scale. The cascade slope $\beta_t$ summarizes the relative magnitude of $V^{(1)}, V^{(2)}, V^{(3)}, V^{(4)}$. Empirically, this summary is robustly negative on SPY (24/24), XLF (24/24), and 99.9\% across 720 parameter combinations.

\textbf{Why HAR misses it.} HAR models persistence in volatility magnitude. The cascade captures the geometric shape of vol across scales. The forecast-encompassing test confirms: the cascade contributes information not in HAR ($p = 0.0055$). The combined model significantly outperforms HAR on all three loss functions.

\textbf{Why multi-scale operators matter.} The cascade is an iterated application of a single operator. Theorem 1 shows the cascade is well-behaved. Theorem 2 shows convergence. Theorem 3 justifies HAC standard errors. Theorem 4 makes the cascade slope scale-invariant.

\textbf{Why the contribution is the cascade, not the neural network.} The Transformer has better squared error but does not contribute information beyond HAR ($p = 0.47$). The cascade does ($p = 0.0055$).

\section{Summary of empirical validation}

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
CER improvement & $+0.138$ \\
Sharpe improvement & $+0.77$ \\
Max DD improvement & $+0.116$ \\
Forecast horizon robustness & all negative \\
\hline
\end{tabular}

\section{What v7 changes (vs v6)}

\textbf{Mathematical (with reviewer's proofs):}
\begin{enumerate}
    \item Theorem 1 rewritten. Uses $O(w^{-2})$ error term. Explicit Gaussian form moved to remark.
    \item Theorem 2 rewritten. Does not identify the limit as 0.
    \item Theorem 3 rewritten. Uses $\alpha$-mixing CLT and HAC consistency.
    \item Theorem 4 rewritten. By induction via positive homogeneity of $D$.
    \item Assumptions 1--3 stated precisely.
\end{enumerate}

\textbf{Empirical:}
\begin{enumerate}
    \item Forecast horizon robustness: $\rho(h)$ for $h = 1, 2, 3, 5, 10, 20$.
    \item CER table with Sharpe, Max DD, Turnover.
    \item Ljung-Box interpretation: "reduced but remains statistically significant."
    \item Tables 1 and 2 split.
    \item MCS interpretation: "cannot be rejected as inferior."
\end{enumerate}

\section*{Acknowledgments}
We thank the anonymous reviewers for the rigorous proofs of Theorems 1 and 2.

\section*{Appendix: Notation}
\begin{itemize}
    \item $\Rproc = \{R_t\}$: log-return process
    \item $D$: rolling std operator
    \item $V^{k}_t = D_t^{k-1}(R_t)$: cascade level
    \item $z^{k}_t$: z-scored $V^{k}_t$
    \item $C_t = (V^{1}_t, \ldots, V^{K}_t)$: cascade
    \item $\beta_t$: cascade slope
    \item $\rho$: variance contraction constant
    \item $V_\beta$: long-run variance of $\beta_t$
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

\bibitem[White(2014)]{White2014}
White, H. (2014). \emph{Asymptotic Theory for Econometricians}. Academic Press.

\bibitem[Billingsley(1995)]{Billingsley1995}
Billingsley, P. (1995). \emph{Probability and Measure}. John Wiley \& Sons.

\bibitem[Hamilton(1994)]{Hamilton1994}
Hamilton, J. D. (1994). \emph{Time Series Analysis}. Princeton University Press.

\bibitem[Ljung and Box(1978)]{LjungBox1978}
Ljung, G. M., and Box, G. E. P. (1978). \emph{Biometrika}, 65(2), 297--303.

\end{thebibliography}

\end{document}
