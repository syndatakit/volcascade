# Comprehensive Paper (12+ pages, 60+ experiments)

**Compiled PDF (12 pages, 310KB):** https://backend.composio.dev/api/v3/sl/DP-hvZooCk

This is the comprehensive version of the paper, with ALL 60+ experiments.

## Correlation matrix (key finding)

The cascade slope is **negatively correlated with HAR** ($-0.38$). The cascade captures information orthogonal to persistence-based forecasting.

| | V1 | V2 | V3 | V4 | Cascade slope | Future RV | HAR-RV |
|---|---|---|---|---|---|---|---|
| Cascade slope | $-0.573$ | $-0.163$ | $+0.211$ | $+0.488$ | $+1.000$ | $-0.184$ | $-0.376$ |
| Future RV | $+0.341$ | $+0.168$ | $+0.139$ | $+0.127$ | $-0.184$ | $+1.000$ | $+0.561$ |
| HAR-RV | $+0.657$ | $+0.324$ | $+0.221$ | $+0.209$ | $-0.376$ | $+0.561$ | $+1.000$ |

## Headline results

- Forecast encompassing: Cascade vs HAR $p = 0.0055$
- Clark-West: $p = 0.019$
- DM: Combined vs HAR wins on MSE, MAE, QLIKE
- CER improvement: $+0.138$
- 24/24 rolling windows negative
- 99.9% negative across 720 parameter combinations

## Files

- paper/README.md
- paper/paper_part1.md
- paper/paper_part2.md
- paper/paper_part3.md
- paper/paper_part4.md
- paper/build_paper.py