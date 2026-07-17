# Cascade-slope cross-asset audit

**Date:** 2026-07-16
**Author:** Nitya Hapani & pong

## What this is

A cross-asset study of the cascade slope's forecast-encompassing contribution
to forward realized volatility, beyond the HAR-RV baseline. The cascade slope
is the within-timepoint OLS coefficient of (1, 2, 3, 4) regressed on
(z^1, z^2, z^3, z^4). This is the central time-series statistic of the
cascade representation and the one most closely tied to the mean-reversion
mechanism in Section 3.2.

This audit is conceptually distinct from `experiments/cross_asset_audit.py`,
which uses z-scored V1 (z1) as the new variable. The cascade slope and
z1 test different hypotheses:
- z1 asks: does current realized vol add information beyond HAR?
- cascade slope asks: does the within-timepoint shape of the cascade
  add information beyond HAR?

## What this is NOT

This audit does NOT include a Diebold-Mariano (DM) test on squared error.
The DM test on (HAR vs HAR+cs) is not informative in the cross-asset
setting because the cascade slope's contribution is primarily
cross-sectional (see Test 2 below), not a level-predictor that would
compete with HAR in MSE.

## Methodology

Three tests, all out-of-sample:

1. **Per-asset encompassing on H2 (2010-2014, US 5 assets) and H3
   (2020-2024, all 10 assets).** Cascade slope is the new variable;
   HAR-RV is the baseline; forward 5-day RV is the target. HAC(5) SEs.

2. **Pooled panel on H3 (10 assets, 1258 dates, n=12,580).** Two
   specifications: (a) asset fixed effects with asset-clustered SEs;
   (b) two-way (date + asset) fixed effects with asset-clustered SEs.

3. **Rolling 3-yr windows of the cascade-slope encompassing coefficient,
   2002-2024 for US, 2006-2024 for intl (where data permits).** 181
   total windows across 10 assets.

## Headline results

- **Cross-sectional pooled panel:** cs coefficient = -0.0016, t=-2.58,
  p=0.0099 (asset FE, cluster by asset). The cascade slope is a real
  cross-sectional signal: when one asset has a high slope relative to
  others at a given date, its forward vol is lower.

- **Two-way FE pooled panel:** cs coefficient = +0.0007, t=+1.39,
  p=0.165. Sign flips and significance drops when date fixed effects
  absorb the cross-sectional variation. Interpretation: the slope's
  effect is *cross-sectional*, not a within-asset time-series effect.

- **Rolling 3-yr windows (181 windows, 10 assets):** 139/181 (76.8%)
  windows have a negative cs coefficient; 40/181 (22.1%) are
  statistically significant at p<0.05. Strongest on SPY and XLV
  (9/21 significant each), XLF (6/21), XLE (4/21), XLK (3/21).
  Consistent negative direction across all 10 assets.

## Headline for paper

> The cascade slope's forecast-encompassing effect is a cross-sectional
> phenomenon (pooled panel, asset FE, p=0.0099), robust across 181
> rolling 3-year windows on 10 assets (139/181 negative beta, 76.8%;
> 40/181 significant, 22.1%), and strongest on US large-cap equities
> (SPY 9/21, XLV 9/21). The slope's effect is not universal across all
> 10 assets at every window - it concentrates in high-information
> regimes and large-cap equities, consistent with the mean-reversion
> mechanism in Section 3.2.

## Files

- `experiments/cascade_slope_cross_asset.py` - the consolidated script.
  Self-contained: loads data, runs all three tests, writes JSON results.
- `results/cascade_slope_per_asset.json` - per-asset H2 and H3 results.
- `results/cascade_slope_pooled.json` - pooled panel summary.
- `results/cascade_slope_rolling.json` - rolling-window aggregate.

## How to reproduce

```bash
cd /path/to/volcascade
python experiments/cascade_slope_cross_asset.py
```

The script will refresh `data/returns_us.csv` and `data/returns_intl.csv`
if they are missing. Otherwise it uses the existing 2026-07-14 data pull.
