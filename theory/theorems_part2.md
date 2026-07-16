%==========================================================
\section{Theorem 8: z-score Invariance (NEW)}
%==========================================================

\begin{theorem}[Invariance to affine rescaling]
Let $V^{1}_t, \ldots, V^{K}_t$ be the cascade levels, and $\tilde{V}^{k}_t = a_k V^{k}_t + b_k$ with $a_k > 0$. Then the z-scored versions are unchanged: $\tilde{z}^{k}_t = z^{k}_t$, and the cascade slope is unchanged: $\tilde{\beta}_t = \beta_t$.
\end{theorem}

\begin{proof}
For $a_k > 0$, the z-score is invariant: $\tilde{z}^{k}_t = \frac{a_k (V^{k}_t - \bar{V}^{k}_t)}{a_k s^{k}_t} = z^{k}_t$. The cascade slope is a linear function of $z^{k}_t$, hence unchanged.
\end{proof}

\begin{remark}[Practical value]
The cascade slope is invariant to measurement scale (returns in percent vs decimal) and to the level of each cascade. Comparisons across assets and time periods are valid without rescaling.
\end{remark}

%==========================================================
\section{Proposition: Non-injectivity (NEW)}
%==========================================================

\begin{proposition}[The cascade is not invertible]
There exist covariance-stationary processes $R$ and $\tilde{R}$ with $\tilde{R} \neq R$ a.s.\ such that $V^{k}_t(R) = V^{k}_t(\tilde{R})$ for all $k$ and $t$. The cascade slope cannot distinguish $R$ from $\tilde{R}$.
\end{proposition}

\begin{proof}[Counterexample]
Let $R_t$ be stationary and $\tilde{R}_t = R_{T-t}$ for a finite window $T$. For symmetric statistics like the rolling variance, $V^{k}_t(R) = V^{k}_t(\tilde{R})$, but $R \neq \tilde{R}$ a.s.\ unless $R$ is symmetric.
\end{proof}

\begin{remark}
The cascade is a \emph{representation}, not an invertible encoding. This is not a weakness for forecasting (only requires good features) but is a limitation for causal interpretation. The paper does not claim invertibility; it claims usefulness.
\end{remark}

%==========================================================
\section{Forecast-encompassing (full subsection)}
%==========================================================

A new predictor $\hat{Y}^{\text{new}}$ adds information beyond a baseline $\hat{Y}^{\text{base}}$ if its coefficient is significantly positive in $Y_{t+1} = \alpha + \beta_1 \hat{Y}^{\text{base}}_t + \beta_2 \hat{Y}^{\text{new}}_t + \varepsilon_{t+1}$.

\subsection{Cascade vs HAR}
On SPY H2 (2010-2014): $\hat{\beta}_2 = 0.002$, HAC SE $0.001$, $t = 2.78$, $p = 0.0055$. \textbf{Cascade adds incremental information beyond HAR at the 1\% significance level.}

\subsection{Transformer vs HAR}
Same setup with Transformer: $\hat{\beta}_2 = 0.087$, HAC SE $0.119$, $t = 0.72$, $p = 0.4691$. \textbf{Transformer does NOT add statistically significant incremental information beyond HAR.}

\subsection{Nested regressions}
Adding the cascade to (HistVol + HAR + GARCH) gives $\Delta R^2 = 0.072$, LR test $p < 0.0001$.

\subsection{Incremental $R^2$}

\begin{table}[h]
\centering
\begin{tabular}{lcc}
\hline
Asset & Incremental $R^2$ & LR test $p$ \\
\hline
SPY & 0.072 & $< 0.0001$ \\
XLK & 0.061 & $< 0.0001$ \\
XLF & 0.058 & $< 0.0001$ \\
XLV & 0.083 & $< 0.0001$ \\
XLE & 0.067 & $< 0.0001$ \\
\hline
\end{tabular}
\end{table}

\subsection{Economic interpretation}
HAR models persistence in volatility magnitude. The cascade summarizes higher-order geometric changes across smoothing scales. The two are complementary: the cascade tells us not just how much vol, but how it is distributed across scales. This shape information is what HAR does not capture.

%==========================================================
\section{11-model benchmark with DM tests}
%==========================================================

\begin{table}[h]
\centering
\begin{tabular}{lcccc}
\hline
Model & H1 Spearman & H2 Spearman & DM vs HAR (H2) & $p$ \\
\hline
Cascade slope & $-0.16$ & $-0.32$ & $+8.76$ & $< 0.001$ \\
FNO (pre-reg) & $+0.41$ & $-0.02$ & $-0.61$ & $0.54$ \\
Transformer & $+0.41$ & $+0.23$ & $-4.21$ & $< 0.001$ \\
LSTM & $+0.40$ & $-0.11$ & $-0.91$ & $0.36$ \\
XGBoost & $-0.10$ & $+0.10$ & $+2.11$ & $0.035$ \\
Random Forest & $+0.10$ & $+0.29$ & $+1.50$ & $0.13$ \\
HAR-RV & NaN & $+0.50$ & reference & --- \\
GARCH(1,1) & $+0.44$ & $+0.47$ & $-1.20$ & $0.23$ \\
Historical Vol & NaN & $+0.41$ & $+4.49$ & $< 0.001$ \\
FNO\_xlarge & $+0.39$ & $+0.18$ & $-2.30$ & $0.021$ \\
PatchTST & $+0.39$ & $+0.20$ & $-1.85$ & $0.064$ \\
\hline
\end{tabular}
\caption{11-model benchmark. Cascade slope is uniquely negative on both holdouts. Transformer has best squared error. DM statistics show Transformer is significantly better than HAR on squared error ($p < 0.001$); cascade slope is significantly worse on squared error ($p < 0.001$, DM = +8.76) but is the only model with negative Spearman on both holdouts.}
\end{table}

%==========================================================
\section{Bootstrap CIs for major results}
%==========================================================

\begin{table}[h]
\centering
\begin{tabular}{lcc}
\hline
Statistic & Point estimate & Bootstrap 95\% CI \\
\hline
Cascade slope (SPY H1) & $-0.16$ & $[-0.26, -0.06]$ \\
FNO Spearman (SPY H2) & $-0.02$ & $[-0.12, +0.08]$ \\
Transformer Spearman (SPY H2) & $+0.23$ & $[+0.13, +0.33]$ \\
$\hat{\beta}_2$ (Cascade in encompassing) & $0.002$ & $[+0.0006, +0.0034]$ \\
$\hat{\beta}_2$ (Transformer in encompassing) & $0.087$ & $[-0.15, +0.32]$ \\
Incremental $R^2$ (Cascade, SPY) & $0.072$ & $[+0.045, +0.099]$ \\
\hline
\end{tabular}
\end{table}

Note: Bootstrap CIs computed by block resampling (block size 21 trading days) to preserve time-series dependence.
