# Paper v2 — LaTeX source

This folder contains the LaTeX source for paper v2 of the VolCascade project.

## Files

- `v2.tex` — Main LaTeX file
- `v2.bib` — Bibliography (embedded in v2.tex as thebibliography)
- `build_paper.py` — Build script (downloads figures, compiles PDF)
- `figures/` — Empty initially. Populated by `build_paper.py`.

## How to build

```bash
cd paper_latex_v2
python3 build_paper.py
```

This will:
1. Download all 8 figures from S3 to `figures/`
2. Run `pdflatex` twice on `v2.tex`
3. Produce `v2.pdf`

Requirements: `pdflatex` (TeX Live), Python 3.

## Figures

- `fig1_pipeline.pdf` — Existing vs new pipeline diagram
- `fig2_benchmark.pdf` — 11-model benchmark table
- `fig3_nested_reg.pdf` — Nested regression table (4 models)
- `fig4_dm_test.pdf` — Diebold-Mariano test statistics
- `fig5_calibration.pdf` — Predicted vs realized vol (SPY 2025+)
- `fig6_fno_explain.pdf` — FNO mode and feature importance
- `fig7_rolling.pdf` — 3-year rolling Spearman (2003-2024)
- `fig8_strategy.pdf` — Vol-targeting strategy backtest

## Section structure

1. Introduction
2. Method (data, cascade, FNO, pre-reg, DM test)
3. Theoretical Results (4 theorems)
4. Empirical Results:
   - 4.1 Main result: cascade slope predicts forward vol
   - 4.2 Robustness: 720 sweep, rolling, bootstrap, cross-asset
   - 4.3 Incremental value: nested regressions, DM test
   - 4.4 Benchmarking: 11 models in one table
   - 4.5 Manifold geometry: crisis days as isolated regions
   - 4.6 Interpretability: FNO modes, feature importance
   - 4.7 Strategy: vol-targeting backtest
5. Discussion
6. Conclusion
Appendices: pipeline diagram, all 8 figures

## Note

This is a separate folder from `paper/v1.md` (which is the markdown version).
If the LaTeX version works well, the markdown version can be deleted.
The user said "we can delete it later".