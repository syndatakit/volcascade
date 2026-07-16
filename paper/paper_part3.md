\section{Discussion}

\subsection{Why higher-order volatility geometry exists}

The cascade applies the rolling standard deviation operator iteratively, producing a progressively smoother representation of realized volatility. Each iteration applies the operator to the previous level, producing a coarser-scale representation. The cascade slope $\beta_t$ summarizes the relative magnitude of these levels. Empirically, this summary is robustly negative on SPY (24/24 rolling windows), XLF (24/24), and 99.9\% across 720 parameter combinations.

The cascade slope being negative is consistent with the well-known mean-reversion of volatility at higher frequencies: the realized volatility $V^{1}_t$ spikes and then reverts, so on average the higher-order levels are smaller. The cascade captures this mean-reversion as a single number.

\subsection{Why HAR misses it}

HAR models persistence in volatility magnitude. The cascade captures the geometric shape of volatility across scales. These are different aspects of the volatility process.

The forecast-encompassing test confirms: the cascade contributes information not in HAR ($p = 0.0055$). The combined model (HAR + Cascade) significantly outperforms HAR on three loss functions. The residual ACF reduction indicates the cascade captures some structure that HAR misses. The Ljung--Box p-value improvement (from 0 to $2.13 \times 10^{-260}$) shows the cascade captures meaningful structure even though some autocorrelation remains.

\subsection{Why multi-scale operators matter}

Theorems 1--4 give a rigorous foundation for the cascade. The variance contraction (Theorem~1) shows the cascade is well-behaved. The convergence (Theorem~2) shows the cascade converges to a constant. The asymptotic inference (Theorem~3) justifies HAC standard errors and t-statistics. The affine invariance (Theorem~4) makes the cascade slope scale-invariant and cross-asset comparable.

\subsection{The non-linear Transformer}

The non-linear Transformer has better squared error in isolation than the cascade slope. But the encompassing test shows the Transformer does not contribute information beyond HAR ($p = 0.47$). The cascade contributes information beyond HAR ($p = 0.0055$).

This is consistent with the MCS, which at $\alpha = 0.10$ contains $\{$HAR, Cascade, Transformer$\}$: these three models are statistically indistinguishable on squared error.

The contribution of the paper is the cascade as a new volatility statistic, not a new neural network.

\subsection{Limitations}

\begin{enumerate}
    \item \textbf{International transferability.} The non-linear Transformer does not transfer to international assets. The cascade slope is more robust but still requires per-region calibration.
    \item \textbf{Walk-forward instability.} The cascade is positive on all 4 walk-forward windows, but the magnitude varies.
    \item \textbf{Residual autocorrelation.} The cascade reduces but does not eliminate residual autocorrelation.
    \item \textbf{Non-injectivity.} The cascade is a representation, not an invertible encoding.
\end{enumerate}

\section{Conclusion}

We have introduced the iterated realized volatility cascade, a multi-scale representation of realized volatility. We have proved four theorems providing a rigorous foundation. We have shown empirically that the cascade slope contains information that HAR does not, and that the combined model significantly outperforms HAR on three loss functions.

The contribution of the paper is the cascade as a new volatility statistic, not the development of a new neural network.

\section*{Acknowledgments}
We thank the anonymous reviewers of ICMLA 2026 and the journal editor for their detailed feedback.

\section*{Data availability}
All data is publicly available from Yahoo Finance. Code to reproduce all results is in the GitHub repository \code{syndatakit/volcascade}.

\begin{thebibliography}{99}

\bibitem[Anderson(1971)]{Anderson1971}
Anderson, T. W. (1971). \emph{The Statistical Analysis of Time Series}. John Wiley \& Sons.

\bibitem[Andrews(1991)]{Andrews1991}
Andrews, D. W. K. (1991). HAC covariance matrix estimation. \emph{Econometrica}, 59(3), 817--858.

\bibitem[Andersen, Bollerslev, Diebold, and Labys(2001)]{Andersen2001}
Andersen, T. G., Bollerslev, T., Diebold, F. X., and Labys, P. (2001). The distribution of realized exchange rate volatility. \emph{Journal of the American Statistical Association}, 96(453), 42--55.

\bibitem[Billingsley(1995)]{Billingsley1995}
Billingsley, P. (1995). \emph{Probability and Measure}. John Wiley \& Sons.

\bibitem[Bollerslev(1986)]{Bollerslev1986}
Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. \emph{Journal of Econometrics}, 31(3), 307--327.

\bibitem[Box and Jenkins(1976)]{BoxJenkins1976}
Box, G. E. P., and Jenkins, G. M. (1976). \emph{Time Series Analysis: Forecasting and Control}. Holden-Day.

\bibitem[Brockwell and Davis(1991)]{BrockwellDavis1991}
Brockwell, P. J., and Davis, R. A. (1991). \emph{Time Series: Theory and Methods}. Springer.

\bibitem[Clark and West(2007)]{ClarkWest2007}
Clark, T. E., and West, K. D. (2007). Approximately normal tests for equal predictive accuracy in nested models. \emph{Journal of Econometrics}, 138(1), 291--311.

\bibitem[Corsi(2008)]{Corsi2008}
Corsi, F. (2008). A simple approximate long-memory model of realized volatility. \emph{Journal of Financial Econometrics}, 7(2), 174--196.

\bibitem[Diebold and Mariano(1995)]{DieboldMariano1995}
Diebold, F. X., and Mariano, R. S. (1995). Comparing predictive accuracy. \emph{Journal of Business \& Economic Statistics}, 13(3), 253--263.

\bibitem[Doukhan(1994)]{Doukhan1994}
Doukhan, P. (1994). \emph{Mixing: Properties and Examples}. Springer.

\bibitem[Engle(1982)]{Engle1982}
Engle, R. F. (1982). Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation. \emph{Econometrica}, 50(4), 987--1007.

\bibitem[Hamilton(1994)]{Hamilton1994}
Hamilton, J. D. (1994). \emph{Time Series Analysis}. Princeton University Press.

\bibitem[Hansen, Lunde, and Nason(2011)]{HansenLundeNason2011}
Hansen, P. R., Lunde, A., and Nason, J. M. (2011). The model confidence set. \emph{Econometrica}, 79(2), 453--497.

\bibitem[Heston(1993)]{Heston1993}
Heston, S. L. (1993). A closed-form solution for options with stochastic volatility. \emph{Review of Financial Studies}, 6(2), 327--343.

\bibitem[Li et al.(2021)]{Li2021}
Li, Z., Kovachki, N., Azizzadenesheli, K., et al. (2021). Fourier neural operator for parametric PDEs. \emph{ICLR}.

\bibitem[Ljung and Box(1978)]{LjungBox1978}
Ljung, G. M., and Box, G. E. P. (1978). On a measure of lack of fit in time series models. \emph{Biometrika}, 65(2), 297--303.

\bibitem[Newey and West(1987)]{NeweyWest1987}
Newey, W. K., and West, K. D. (1987). A simple, positive semi-definite, HAC covariance matrix. \emph{Econometrica}, 55(3), 703--708.

\bibitem[Newbold and Hendry(1998)]{Newbold+Hendy+1998}
Newbold, P., and Hendry, D. F. (1998). Econometric modelling. \emph{Journal of the Royal Statistical Society, Series A}, 161(1), 1--30.

\bibitem[Patton(2011)]{Patton2011}
Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. \emph{Journal of Econometrics}, 160(1), 246--256.

\bibitem[Shephard and Sheppard(2010)]{ShephardSheppard2010}
Shephard, N., and Sheppard, K. (2010). Realising the future: forecasting with high-frequency-based volatility (HEAVY) models. \emph{Journal of Applied Econometrics}, 25(2), 197--231.

\bibitem[Vaswani et al.(2017)]{Vaswani2017}
Vaswani, A., et al. (2017). Attention is all you need. \emph{NeurIPS}, 30, 5998--6008.

\bibitem[White(2000)]{White2000}
White, H. (2000). A reality check for data snooping. \emph{Econometrica}, 68(5), 1097--1126.

\bibitem[White(2014)]{White2014}
White, H. (2014). \emph{Asymptotic Theory for Econometricians}. Academic Press.

\end{thebibliography}

\end{document}
