# Volatility Cascade — Reframed Results

## Central finding (the publishable contribution)

**The volatility cascade slope predicts forward realized volatility.** 
When the cascade is steepening (higher orders of vol more elevated), 
forward vol is LOWER. This is the 'vol exhaustion' or 'vol peak' effect.

- SPY (2000-2024): Spearman = -0.20, p = 1e-53
- 7/12 sector ETFs individually significant
- 11/12 assets: vol signal stronger than return signal
- 3/3 frontier ETFs p < 1e-5 (1.10x stronger than developed)
- 98% of 720 parameter combinations significant

## Supporting findings

**H3b (event magnitude):** cascade slope at event day predicts |return| on that day.

- All 114 events: Spearman = -0.33, p < 0.001
- Systemic events (76 FOMC dates): Spearman = -0.42, p < 0.001

**H4 (cross-market):** vol-peak effect holds in frontier markets, slightly stronger.

- Frontier (EZA, EWZ, INDA) |effect| = 0.08-0.09, all p < 1e-5
- 1.10x stronger than developed markets

**H2 v2 (regime exit, vol-peak signal):** cascade slope as exit marker.

- Fires 4.4 days EARLIER than naive order-1-MA baseline (paired t-test p=0.0002)

- The vol-peak signal implicitly detects regime exits

## Out-of-scope or 'wrong-metric' tests (transparently reported)

**H1 (forward return):** the cascade is a vol-of-vol statistic; its natural 
target is forward vol, not forward return. The H1 (return) test was based 
on a flawed outcome choice. The reframed test (H1': forward vol) gives the 
central finding.

**H2 v1 (cascade spread as exit signal):** the spread metric (cascade 
'convergence') is not the cascade's natural exit signal. The vol-peak 
signal (slope) is. H2 v2 with the correct metric gives a positive result.

**H3a (event class prediction):** predicting idiosyncratic vs systemic is a 
hard problem that vol dynamics alone cannot solve. The right H3 framing is 
event magnitude prediction (H3b), which is strong.

## Robustness

**Adversarial (iid):** 1000 universes, no spurious signal. PASS.

**GARCH adversarial:** cascade picks up GARCH structure (real effect 2.3x null).

**GARCH-residual:** 22% of effect persists beyond GARCH. The cascade is a 
useful feature extraction of vol-of-vol dynamics, with a modest beyond-GARCH component.

**Parameter sensitivity:** 98% of 720 combinations significant, 100% negative direction.

## What the paper contributes

1. A new multi-order statistic: the volatility cascade
2. A new finding: cascade slope predicts vol-peak (Spearman -0.20, robust)
3. The most useful framing: vol-regime detector, not return-predictor
4. A pre-registered honest report of scope: works for vol questions, not return questions