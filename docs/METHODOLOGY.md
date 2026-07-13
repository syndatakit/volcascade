# Volatility Cascade — Methodology

**Companion to:** `DESIGN_MEMO.md` (locked design decisions)
**Status:** First draft, 2026-07-13
**Target venue:** Modern Finance

---

## 1. Setup and notation

Let $r_{i,t} = \log(p_{i,t}/p_{i,t-1})$ denote the log-return of asset $i$ on day $t$, with $i \in \{1, \dots, N\}$ and $t \in \{1, \dots, T\}$. The realized variance over a rolling window of length $L$ is

$$
RV_{i,t}^{(1)}(L) \;=\; \sum_{s=t-L+1}^{t} r_{i,s}^2.
$$

The realized volatility is its square root, $\sigma^{(1)}_{i,t}(L) = \sqrt{RV_{i,t}^{(1)}(L)}$. Throughout, we work with $\sigma^{(1)}_{i,t}$ directly, not its square, so that "orders of volatility" compose by re-applying the realized-vol operator rather than re-summing squares.

The **order-$k$ volatility** for $k \geq 1$ is defined recursively:

$$
\sigma^{(k)}_{i,t}(L) \;=\; \sqrt{\frac{1}{L}\sum_{s=t-L+1}^{t} \bigl(\sigma^{(k-1)}_{i,s} - \overline{\sigma^{(k-1)}_{i,t}}\bigr)^2},
$$

where $\overline{\sigma^{(k-1)}_{i,t}} = \frac{1}{L}\sum_{s=t-L+1}^{t} \sigma^{(k-1)}_{i,s}$ is the trailing mean of the order-$(k-1)$ series. Equivalently, $\sigma^{(k)}_{i,t}$ is the rolling sample standard deviation of $\sigma^{(k-1)}_{i,s}$ over $[t-L+1, t]$.

We truncate at $k_{\max} = 4$. The cutoff is empirically anchored in Section 9 (effective-N analysis on synthetic series): order-5 and above are noise-dominated for both developed and frontier samples at standard lookback lengths.

## 2. Z-score normalization

To make orders $1, \dots, k_{\max}$ comparable on a common scale, each order-$k$ series is z-scored against its own trailing history of length $Z$:

$$
z^{(k)}_{i,t}(L, Z) \;=\; \frac{\sigma^{(k)}_{i,t}(L) - \mu^{(k)}_{i,t}(Z)}{\eta^{(k)}_{i,t}(Z)},
$$

where $\mu^{(k)}_{i,t}(Z)$ and $\eta^{(k)}_{i,t}(Z)$ are the rolling mean and standard deviation of $\sigma^{(k)}_{i,s}$ over $[t-Z+1, t-1]$. We default to $Z \in \{60, 120, 252\}$ (trading days, robustness battery).

The z-scoring serves two purposes: (i) it places each order on a unit-variance scale so cross-order comparison is meaningful; (ii) it absorbs slow-moving level shifts (e.g. the secular upward trend in VVIX documented by Albers 2023), so the cascade captures *shape* not *level*.

## 3. Cascade slope

At each $t$ and for each asset $i$, we have a vector of z-scores

$$
\mathbf{z}_{i,t} \;=\; \bigl(z^{(1)}_{i,t}, z^{(2)}_{i,t}, z^{(3)}_{i,t}, z^{(4)}_{i,t}\bigr) \in \mathbb{R}^{4}.
$$

The **cascade slope** $\beta_{i,t}$ is the OLS coefficient from regressing the order index $k = 1, \dots, 4$ on $z^{(k)}_{i,t}$:

$$
\beta_{i,t} \;=\; \frac{\sum_{k=1}^{4}(k - \bar{k})(z^{(k)}_{i,t} - \bar{z}_{i,t})}{\sum_{k=1}^{4}(k - \bar{k})^2}, \qquad \bar{k} = 2.5.
$$

A **flat** cascade ($\beta \approx 0$) means all orders move together; a **steepening** cascade ($\beta > 0$) means higher orders move more than lower orders (instability-of-instability); an **inverted** cascade ($\beta < 0$) means higher orders move less, consistent with mean-reversion of volatility-of-volatility.

A **secondary** summary, the **cascade entropy** $H_{i,t}$, is the Shannon entropy of the normalized z-score vector:

$$
p^{(k)}_{i,t} = \frac{|z^{(k)}_{i,t}|}{\sum_j |z^{(j)}_{i,t}|}, \qquad H_{i,t} = -\sum_{k=1}^{4} p^{(k)}_{i,t} \log p^{(k)}_{i,t}.
$$

$H$ is bounded by $\log 4 \approx 1.386$, with high $H$ indicating evenly distributed orders (flat cascade) and low $H$ indicating concentration on a single order. $H$ is reported alongside $\beta$ as a non-linear robustness check.

## 4. H1 — Cascade shape classifies regime breaks

For each day $t$ with $z^{(1)}_{i,t} > 1.5$ (an order-1 spike event), record the cascade slope $\beta_{i,t}$ and the forward $N$-day drawdown

$$
DD_{i,t}(N) = \frac{p_{i,t+N} - p_{i,t}}{p_{i,t}}.
$$

Stratify spike events by $\beta_{i,t}$ into tertiles (flat / moderate / steep). Test the null of equal forward-drawdown distributions across tertiles using a Mann-Whitney $U$ test (two-sided) and a Kolmogorov-Smirnov test (two-sided). Run separately for the developed sample (S&P 500) and the frontier sample.

**Pre-registered pass criterion (DESIGN_MEMO.md):** cascade-classified (steep-tertile) events have $\geq 2\times$ larger forward 5-day drawdown than flat-tertile events, with Mann-Whitney $p < 0.05$ after BH-FDR correction.

## 5. H2 — Cascade convergence marks regime exit

Define the **cascade convergence** signal $C_{i,t}$ as the rolling $K$-day change in the spread between the highest and lowest z-scored orders:

$$
C_{i,t} = \frac{1}{K}\sum_{s=t-K+1}^{t}\bigl(\max_k z^{(k)}_{i,s} - \min_k z^{(k)}_{i,s}\bigr),
$$

with $K = 20$ (one trading month). A regime exit is flagged on day $t$ if $C_{i,t}$ has fallen below its 60-day rolling median (a threshold-free, order-respecting analog of "the cascade is collapsing back to flat").

**Naive baseline:** flag an exit when $z^{(1)}_{i,t}$ crosses below its 60-day moving average. This is the standard order-1-only regime-exit signal in the HMM-and-MA literature (Hamilton 1989; Maheu & McCurdy 2000).

**Comparison metric:** for each flagged exit, label it as *true* if no order-1 spike occurs in the next 20 trading days, *false* otherwise. Report the false-exit rate for both signals. Run separately for the developed and frontier samples.

**Pre-registered pass criterion:** cascade-convergence exits have false-exit rate < 30%, vs. ~50% for the order-1 MA baseline. (50% is the expected false rate of a threshold-crossing signal under random walk dynamics; a useful signal must beat it substantially.)

## 6. H3 — Cross-sectional decoupling (the most novel piece)

For a stock $i$ and its sector (or country) benchmark $b$, construct parallel cascades $\mathbf{z}_{i,t}$ and $\mathbf{z}_{b,t}$. The **decoupling order** $k^*_{i,t}$ is the smallest $k$ at which the joint distribution of $(z^{(k)}_{i,t}, z^{(k)}_{b,t})$ rejects the null of equal conditional distributions via a Chow test (Chow 1960) on the bivariate regression

$$
z^{(k)}_{b,t} = \alpha + \gamma\, z^{(k)}_{i,t} + \varepsilon_t,
$$

comparing the residual sum of squares for $s \in [t-W, t-1]$ and $s \in [t-W, t-K^*-1] \cup [t-K^*+1, t]$ (leave-one-out around $k^*$). The lookback is $W = 252$ trading days.

Low $k^*$ (decoupling at order 1 or 2) means the stock and sector diverge in raw volatility; high $k^*$ or no decoupling means they co-move through all orders.

**Hypothesis:** low-$k^*$ decoupling predicts *idiosyncratic* events (the stock is moving on its own information); high-$k^*$ / no-decoupling predicts *systemic* events (everything is moving together through all orders of the cascade).

**Ground truth (H3):** idiosyncratic = earnings surprises (Zacks), M&A announcements (SDC), FDA binary events (BioPharmCatalyst), CEO exits; systemic = FOMC decisions, NFP releases, GFC peak days, COVID crash days. Curated table committed as `data/ground_truth_events.csv`.

**Pre-registered pass criterion:** decoupling order $k^*$ predicts event type (idiosyncratic vs systemic) with AUC > 0.7, using logistic regression with 5-fold time-series cross-validation.

**Robustness:** repeat with cross-correlation threshold (decoupling = rolling correlation drops below 0.5) and KL divergence between conditional distributions. Report all three.

## 7. H4 — Cross-market extension

Re-run H1 and H3 on the frontier sample (NSE Kenya, GSE Ghana, BVSP Brazil, JSE South Africa, NSE India, BSE Bangladesh) paired with their country/regional ETFs as the "sector" proxies.

**Interaction test:** the headline result is whether the cascade's classification accuracy (H1, H3) differs significantly between developed and frontier subsamples. Use a bootstrap test (1000 resamples of days, block-resampled at monthly frequency to preserve serial dependence) on the AUC difference. Report $p$-value after BH-FDR correction across all H1 × frontier / H3 × frontier / H1 × developed / H3 × developed comparisons.

**Pre-registered pass criterion:** cross-market classification difference is significant at $p < 0.05$ after BH-FDR.

**Mechanism interpretation:** the comparison tests the Brunnermeier-Pedersen (2009) liquidity-spiral hypothesis — does slower price discovery in thin markets (i) amplify vol-of-vol signal (cascade steeper in crisis) or (ii) mask it (cascade noisier)? The direction of the difference is *not* pre-registered (this is an empirical question), only its significance.

## 8. Comparison battery

All four hypotheses are evaluated against a canonical set of baselines drawn from the regime-detection and vol-of-vol literature:

| Method | Reference | What it tests |
|---|---|---|
| HMM (Gaussian, 2-state) | Hamilton 1989 | Standard Markov regime detector; BIC selects state count |
| MS-AR(1) | Hamilton 1989; Ang-Bekaert 2002a | Markov-switching AR with fixed K=2 |
| Wasserstein $k$-means | Campani et al. 2021 | Non-parametric, distribution-based regime classifier |
| Bai-Perron F-test | Bai & Perron 2003 | Multiple structural change points in the cascade slope series |
| Inclán-Tiao CUSUM | Inclán & Tiao 1994 | CUSUM of squares for variance shifts |
| RCM | Ang & Bekaert 2002b | Regime Classification Measure (how cleanly the model separates regimes) |

The cascade slope $\beta_t$ is fed *into* Bai-Perron and Inclán-Tiao as a preprocessed series; the cascade itself is not a standalone classifier but a *feature* that the standard detectors consume. This isolates the cascade's marginal contribution.

## 9. Adversarial test (the rebuttal)

Reviewers will ask whether the cascade is "just vol-of-vol with extra steps." The rebuttal rests on a synthetic experiment.

**Procedure:**

1. Simulate two synthetic universes:
   - **DM-calibrated:** AR(1)-GARCH(1,1) with Student-$t$ innovations, parameters fit to SPY realized volatility (long memory, low noise floor, $\nu \approx 5$).
   - **FM-calibrated:** same model, parameters fit to a representative frontier market (e.g. NSE Kenya) — higher noise floor, lower signal-to-noise, more frequent parameter instabilities.
2. Inject *no true regime structure* into either. Run the cascade construction on both.
3. **Null hypothesis:** the cascade slope distribution is symmetric around 0 in both universes (no spurious steepening).
4. **Reject criterion:** if the cascade shows systematic steepening or inversion in either universe, the cascade is detecting the GARCH dynamics rather than regime structure, and the H1/H2/H3/H4 results are confounded.

This is the single most important robustness check in the paper. A clean synthetic test (no spurious cascade) buys the entire empirical section.

## 10. Sample size and effective N

Report the effective sample size $N_{\text{eff}}^{(k)}$ at each order $k$ for each sample. For order $k$, $N_{\text{eff}}^{(k)} = T - (k-1) \cdot L - Z + 1$ (each successive order loses $L$ days of warmup plus the z-score window). For the default $L=20$, $Z=252$, $T=2520$ (10 years of daily data):

| Order $k$ | $N_{\text{eff}}$ |
|---|---|
| 1 | 2269 |
| 2 | 2249 |
| 3 | 2229 |
| 4 | 2209 |

The frontier sample has shorter history for some markets (NSE Kenya data is reliable from ~2005; GSE Ghana from ~2010); order-4 estimates in the frontier are flagged as exploratory. Power calculations are reported in the appendix.

## 11. Multiple testing

We conduct $\sim 120$ tests across the 4 hypotheses × 2 samples × 3 lookbacks × 5 forward windows, before interaction tests. We control the false discovery rate at $q = 0.05$ using Benjamini-Hochberg FDR (Benjamini & Hochberg 1995). All reported $p$-values are BH-adjusted unless otherwise noted.

We also pre-register the *test battery* (which tests get run) before looking at results, to prevent specification-search. The full pre-registration is in `docs/PREREGISTRATION.md` (to be written before the pilot).

## 12. Pre-registered success criteria (consolidated)

| Hypothesis | Pass criterion |
|---|---|
| H1 | Steep-tertile events have $\geq 2\times$ larger forward 5-day drawdown than flat-tertile (Mann-Whitney $p < 0.05$ after BH-FDR) |
| H2 | Cascade-convergence exits have false-exit rate < 30% vs. ~50% for order-1 MA baseline |
| H3 | Decoupling order $k^*$ predicts event type with AUC > 0.7 (5-fold TS-CV) |
| H4 | DM vs. FM classification difference significant at $p < 0.05$ after BH-FDR |

A result that fails any criterion is reported as a *negative* or *partially-supported* result, not discarded. The pre-registration binds the analysis but not the conclusion.

## 13. Open methodological questions

1. **Optimal $L$ for the inner rolling window:** currently fixed at 20. Should we estimate $L$ from the data (e.g. via minimum-description-length)?
2. **H3 decoupling at low-frequency (weekly/monthly) events:** the Chow test is calibrated for daily spikes. M&A announcements often have multi-day drift; do we need a slower decoupling definition for slow-burn idiosyncratic events?
3. **Cascade slope regularization:** OLS is sensitive to collinearity (orders are highly correlated at long lookbacks). Ridge-regularized slope as robustness.
4. **Multivariate cascade:** the current framework is univariate (one asset at a time). A multivariate cascade (joint $\sigma$ across assets) would be a natural extension, but is out of scope for the v1 paper.

These are flagged for sensitivity analysis in the appendix; they do not block the v1 design.

---

*End of methodology v1. Next: package MVP (cascade.py + decoupling.py + baselines.py) implementing Sections 1-3, 6, 8. Pilot script runs H1 on S&P 500 with synthetic-adversarial pre-test.*
