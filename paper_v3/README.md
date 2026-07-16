# Full Paper COMPREHENSIVE v5 (56 pages, operator selection)

**Compiled PDF (56 pages, 545KB):** https://backend.composio.dev/api/v3/sl/okMP4zqomP

## NEW in v5: Operator Selection section (4 pages)

Addresses the biggest scientific risk: why rolling standard deviation and not other operators (variance, MAD, bipower, realized kernel, IQR, entropy)?

### Operator comparison (SPY 2010-2024)

| Operator | Spearman |
|----------|----------|
| **std** | **-0.2096** |
| IQR | -0.1465 |
| MAD | -0.1386 |
| realized_kernel | -0.1072 |
| variance | -0.0647 |
| bipower | -0.0516 |
| entropy | +0.0373 |

### Theoretical property table

Standard deviation is the unique combination of:
1. Positive homogeneity of degree 1
2. Z-score invariance (cascade slope dimensionless)
3. Smoothness and differentiability (Theorems 1, 3 work)
4. Computational efficiency (0.34s, fastest)
5. Empirical performance (best Spearman)

No other operator has all 5 properties.

## Structure (56 pages)

- 1 Introduction (3 pages)
- 2 Background and Preliminaries (4 pages)
- 3 Cascade Representation (3 pages)
- 4 Theoretical Properties (5 pages)
- 5 Connection to Volatility Literature (3 pages)
- 6 Methodology (3 pages)
- 7 Comprehensive Empirical Results (10+ pages)
- 8 Discussion (3 pages)
- 9-22 New sections and appendices
- 23 Operator Selection (NEW, 4 pages)
- 24 Why the cascade is the right representation
- References (45+)
- Appendices

## How to compile

```bash
cd paper_v3
python3 build_paper.py
pdflatex paper.tex
```