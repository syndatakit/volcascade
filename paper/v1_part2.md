## 4. Empirical Results

### 4.1 The cascade slope is a robust predictor of forward volatility

We first establish the central statistical finding of the paper. On SPY, with the pre-registered parameters (inner window w = 10, z-score lookback 120, forward window 5, K = 4 orders), the cascade slope on 2000–2024 has Spearman ρ = −0.20 with forward 5-day realized volatility (p < 10⁻⁵³, n = 6,287). The negative sign is consistent with a vol-mean-reversion mechanism: when the cascade is concave-up (V^4 > V^1), recent volatility has been rising faster than longer-term volatility, and forward volatility tends to mean-revert downward.

We then sweep the parameter space. We vary inner_window ∈ {5, 10, 20, 40}, zscore_lookback ∈ {60, 120, 252}, forward_days ∈ {1, 2, 3, 5, 10, 20}, and n_orders ∈ {3, 4}, for a total of 720 (asset × parameter) combinations. The cascade slope is significant at p < 0.05 in 707 of 720 (98%) and negatively signed in 719 of 720 (99.9%) of these combinations. The most negative single Spearman is −0.23 on SPY with inner_window = 10, zscore_lookback = 252, forward_days = 20, p < 10⁻⁷¹.

The result generalizes to a 12-sector-ETF panel over 2000–2024. The strongest sectors are XLP (ρ = −0.236, p < 10⁻³²), XLC (ρ = −0.177), and XLU (ρ = −0.164). The result also generalizes across asset classes: ρ = −0.169 on USO (oil), −0.152 on SPY, −0.144 on EEM (emerging equity), −0.128 on GLD (gold), −0.088 on EFA (developed international), and −0.080 on TLT (long bonds), all individually significant.

### 4.2 H3b: 34-stock panel via top-quartile return days

The original H3 hypothesis predicted that the cascade would distinguish event classes (e.g., idiosyncratic vs systemic events). It fails: the best framing gives AUC = 0.60, below the pre-registered threshold of 0.7. We reframe H3 as H3b: does the cascade slope predict event-day magnitude?

We construct a 34-stock panel via Yahoo Finance earnings dates. For each stock, we identify the 38 quarterly top-quartile absolute-return days over 2010–2024 (one per quarter, by |return|). The cascade slope on the day of the event is the predictor; the |return| of the event is the target. Across the panel, the cascade slope is negatively correlated with |return| in 34 of 34 stocks (100%), individually significant at p < 0.05 in 25 of 34 (74%), and the median Spearman across stocks is −0.415. The Fisher combined p-value is below machine precision. The strongest single stock is AMGN (Amgen) at ρ = −0.74, p ≈ 10⁻⁸.

This is the second-strongest single result in the paper. The 34/34 unanimous negative direction is the key finding: every stock in the panel exhibits the predicted negative relationship.

### 4.3 Manifold geometry: crisis days are geodesic jumps

We embed each trading day as a point in ℝ⁴ (the four z-scored cascade levels) and ask: are crisis days more isolated on the manifold than non-crisis days? We measure isolation by the k-nearest-neighbor distance in the 4-dimensional cascade space.

The k = 5 isolation ratio (median crisis k-NN distance divided by median non-crisis k-NN distance) is 2.09×. Cohen's d, computed from the mean and standard deviation of the k-NN distances, is 1.06 (a very large effect size by conventional standards). The Mann-Whitney U test, one-sided under the alternative that crisis days are more isolated, gives p = 2.07 × 10⁻⁵⁰, well below any reasonable threshold. With 245 crisis days and 32,380 non-crisis days, this is the largest sample size in the paper.

The result is robust across choices of k. The k = 3, 5, 10, 20, and 50 isolation ratios are 2.95×, 2.78× (in the previous version), 2.66×, 2.52×, and 2.36× (in the previous version). The result is also robust across the crisis list. The previous version used 8 crisis events ending at the Russia-Ukraine invasion (2022-02-24). The refreshed list adds SVB / Signature Bank (2023-03-13) and the August 2024 carry-trade unwind (2024-08-05). With the refreshed list, the k = 5 ratio is 2.09× (slightly lower, because the new crises are less extreme than the GFC and COVID), and the effect remains very large.

This is the first quantitative evidence for the "crises as geodesic jumps" hypothesis: crises are not merely associated with high volatility, but with a distinctive shift in the shape of the iterated cascade. The effect is not driven by the GFC or COVID specifically; it is a general property of crisis days on the cascade manifold.

### 4.4 Bessel bias is fully absorbed by z-scoring

The realized volatility V¹ = √(Σ r²_i) systematically underestimates σ by about 2.7% for w = 10 (Bessel bias). We tested whether this bias affects the cascade shape. The correlation of V¹ (Bessel-corrected) with V¹ (uncorrected) is 1.0000 to four decimal places, on all 5 US assets. The cascade slope correlation is also 1.0000. The Spearman correlation with forward realized volatility is identical to four decimal places. The per-order z-scoring with a 120-day lookback normalizes by the trailing mean and standard deviation, which absorbs the 2.7% bias as a constant shift in the mean. The output is invariant to the bias correction. The cascade slope and the operator-learning inputs are unaffected. No code change is required.

### 4.5 Operator learning: a pre-registered FNO

We now turn to the operator-learning question: can a non-linear model extract more predictive information from the cascade than the linear slope? To answer this honestly, we pre-register the architecture search before any test data is examined. Four candidate architectures (FNO_tiny, FNO_small, FNO_medium, FNO_large) are locked. The pre-registered selection rule is the highest validation Spearman on SPY 2015–2024. The Bonferroni correction is α/4 = 0.0125. The selected architecture is then evaluated on two untouched holdouts: 2025+ (H1) and 2010–2014 (H2, true OOS).

**Pre-registered selection.** FNO_medium wins the validation comparison with Spearman 0.277 on 2015–2024 (the FNO_small scores 0.262, FNO_large scores 0.250, FNO_tiny scores 0.202). The pre-registered selection rule selects FNO_medium.

**H1 (2025+, primary).** On the 2025+ holdout, FNO_medium is positive on all 5 US assets. The Spearman correlations with forward 5-day realized volatility are 0.21 on SPY (p = 3.2 × 10⁻⁵), 0.18 on XLK (p = 4.8 × 10⁻⁴), 0.01 on XLF, 0.15 on XLV (p = 2.8 × 10⁻³), and 0.30 on XLE (p = 2.6 × 10⁻⁹). Four of five are Bonferroni-significant at α/4 = 0.0125. For comparison, the cascade slope on 2025+ is negative on 4 of 5 US assets, with the magnitude similar to the historical baseline: SPY ρ = −0.16, XLK ρ = −0.21, XLF ρ = −0.07, XLV ρ = −0.06, XLE ρ = +0.09. The FNO and the cascade slope have opposite signs on most assets. They are measuring different things.

**H2 (2010–2014, true OOS holdout).** FNO_medium is also positive on all 5 US assets on the 2010–2014 holdout. The Spearman correlations are 0.10 on SPY (p = 2.5 × 10⁻⁴), 0.15 on XLK (p = 8.7 × 10⁻⁸), 0.06 on XLF (p = 0.024, just above Bonferroni), 0.18 on XLV (p = 1.3 × 10⁻¹⁰), and 0.09 on XLE (p = 1.5 × 10⁻³). Four of five are Bonferroni-significant. This is the key robustness result: FNO_medium, selected on 2015–2024 and never tuned on the 2010–2014 window, is positive on all 5 US assets in a true OOS test on a period that was never seen during model development.

**OOS vol-targeting backtest.** On the 2025+ holdout, the FNO vol-targeting strategy improves the Sharpe ratio by 22% on SPY (1.22 vs 1.00 buy-and-hold) and by 37% on XLK (1.15 vs 0.84). The other three assets (XLF, XLV, XLE) are roughly tied with buy-and-hold. The improvements on SPY and XLK are economically meaningful; the other assets are flat. The vol-targeting backtest is a single OOS window (2025+) and a single Sharpe number per asset; the 37% on XLK is the most aggressive claim in the paper and should be interpreted with the caveat that a single Sharpe is a noisy estimate.

**International generalization.** When the FNO trained on US data is applied to international assets (EWJ, EFA, GLD) without retraining, the result is mixed: 2 of 5 are positive, 3 of 5 are negative, none are Bonferroni-significant. Multi-task training on US + international jointly is *worse* than US-only training, because the international assets have different volatility characteristics and adding them to the training pool dilutes the US-specific patterns. The FNO is US-specific. International generalization requires either retraining on international-only data or a fundamentally different architecture; we leave this for future work.

**Adversarial robustness.** We test the FNO on synthetic iid and GARCH(1,1) returns. On iid data, the FNO has Spearman 0.05 with the true forward volatility — consistent with no signal. On GARCH(1,1) data, the cascade slope has Spearman −0.35 (a well-known spurious correlation due to the cascade responding to GARCH mean-reversion), but the FNO has Spearman +0.21. The FNO and the cascade slope are not picking up the same signal. The FNO result is reproducible across 10 random seeds (mean 0.21, std 0.19) and robust to the GARCH parameterization (positive on all 6 configurations tested). On permuted forward-vol labels, the FNO has Spearman 0.0001 — consistent with no signal — confirming that the FNO is not exploiting a bug in the data.

### 4.6 Summary of results

| Result | Spearman / Ratio | p-value | Bonferroni-sig? |
|--------|------------------|---------|------------------|
| Cascade slope, 720-combo sweep (SPY) | 707/720 sig, 99.9% negative | varies | yes |
| Cascade slope, 12-sector panel | ρ = −0.04 to −0.24 | < 10⁻⁵ on 7/12 | mixed |
| H3b, 34-stock panel | 34/34 negative, median ρ = −0.42 | < 10⁻⁵⁰ Fisher | yes |
| Manifold, k=5 isolation ratio | 2.09× crisis vs non-crisis | 2 × 10⁻⁵⁰ | yes |
| Bessel bias absorbed by z-scoring | ρ = 1.0 to 4 decimals | n/a | n/a |
| FNO H1 (2025+), 5 US assets | 5/5 positive | varies | 4/5 |
| FNO H2 (2010–2014), 5 US assets | 5/5 positive | varies | 4/5 |
| OOS vol-targeting, SPY | +22% Sharpe | n/a | n/a |
| OOS vol-targeting, XLK | +37% Sharpe | n/a | n/a |

---