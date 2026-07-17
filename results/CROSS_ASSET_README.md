# Cross-asset forecast-encompassing audit

**Date:** 2026-07-16
**Author:** Nitya Hapani & pong

## What this is

A cross-asset study of the cascade's forecast-encompassing contribution.
The single-asset result on SPY is extended to 5 US assets (H2 2010-2014)
and 10 assets total (H3 2020-2024, 5 US + 5 intl).

The new variable tested is z-scored V1 (z1), the first level of the cascade
(z-scored realized volatility). This is a component of the cascade
representation but is conceptually distinct from the cascade slope beta_t,
which is a separate time series computed as the within-timepoint OLS slope
of (1, 2, 3, 4) on (z^1, z^2, z^3, z^4). Both are part of the cascade
representation; they test different hypotheses.

## What this is NOT

This audit does **not** include the Diebold-Mariano (DM) test. The DM test
on (HAR vs HAR+z1) shows that z1 does not significantly improve
out-of-sample MSE on 5-year windows for any of the 10 assets. This is
consistent with the broader vol-forecasting literature, where RV persistence
makes MSE improvements hard to obtain.

## Headline results

**Forecast-encompassing, H2 2010-2014 (5 US assets):** 5/5 significant
(p<0.05), 5/5 positive beta.

**Forecast-encompassing, H3 2020-2024 (all 10 assets):** 10/10 significant,
10/10 positive beta.

**Pooled panel (10 assets, 1258 dates, n=12,580):** z1 coefficient = +0.0067
(t=8.87, p=7.4e-19) with asset fixed effects. Significant (t=3.44, p=0.0006)
even under two-way (date+asset) fixed effects with asset-clustered SEs.

## Files

- `experiments/cross_asset_audit.py` - the consolidated script.
- `results/cross_asset_encompassing.json` - per-asset encompassing results.
- `results/cross_asset_panel.json` - pooled panel with asset FE and
  two-way FE.

## How to reproduce

```bash
cd /path/to/volcascade
python experiments/cross_asset_audit.py
```
