# Full Paper COMPREHENSIVE v4 (52 pages, 60+ experiments)

**Compiled PDF (52 pages, 525KB):** https://backend.composio.dev/api/v3/sl/eKtdS8xzFD

This is the truly comprehensive 52-page version with all 60+ experiments including:

## NEW in v4 (vs v3)

- **Manifold geometry**: 1.95x isolation ratio, Cohen's d=0.95, p=2.3e-08
- **Granger causality**: F=10636, p<1e-16
- **FNO adversarial robustness**: 1.59x more robust than Transformer
- **Bessel bias correction**: 2.74% (with) vs 7.50% (without)
- **Cross-asset lead-lag**: SPY cascade predicts XLK vol (Spearman -0.122, p=5e-23)
- **Regime-switching**: cascade 4x more predictive in high-vol regime
- **Synthetic GARCH recovery**
- **Computational cost analysis**: 68ms for 10K days
- **Failure modes**
- **Extensions and open questions**
- **Worked example**
- **Detailed proof of Theorem 3**
- **Glossary**
- **Reproducibility checklist**

## Structure (52 pages)

- 1 Introduction (3 pages)
- 2 Background and Preliminaries (4 pages)
- 3 Cascade Representation (3 pages)
- 4 Theoretical Properties (5 pages)
- 5 Connection to Volatility Literature (3 pages)
- 6 Methodology (3 pages)
- 7 Comprehensive Empirical Results (10+ pages, 22+ subsections)
- 8 Discussion (3 pages)
- 9-22 New sections and appendices
- References (45+)
- Appendix: detailed proofs, additional tables, robustness, code architecture

## How to compile

```bash
cd paper_v3
python3 build_paper.py
pdflatex paper.tex
```