# Experiment scripts (2026-07-16)

This folder contains the 8 experiment scripts used in the 2026-07-16 sessions.

## Scripts

| File | What it does |
|------|--------------|
| `all_fixes.py` | Extended pre-reg with 8 architectures (FNO_tiny, FNO_small, FNO_medium, FNO_large, FNO_xlarge, Transformer, NBEATS, PatchTST). Transformer wins pre-reg. |
| `all_fixes2.py` | International with Transformer, real OOS strategy, DM test. |
| `fix_v3.py` | Better real strategies (vol-targeting + vol-timing), per-region Transformer, walk-forward. Vol-timing is 3/5 wins vs B&H. |
| `fix_strategy.py` | Real OOS strategy fix (clipped vol predictions). |
| `intl_dm.py` | International Transformer + DM test (Transformer wins on all 5 US). |
| `intl_only.py` | International with adjusted splits for intl data. |
| `intl_v2.py` | International with adjusted train/val/test (2010-2016 train, 2017-2019 val, 2020-2024 test). |
| `make_figures.py` | Generate 4 figures: pipeline diagram, benchmark table, nested regression, DM test. |
| `make_figs_2.py` | Generate 4 more figures: calibration, FNO explainability, rolling stability, strategy backtest. |

## How to run

```bash
# Install dependencies
pip install torch yfinance scipy scikit-learn xgboost arch matplotlib --index-url https://download.pytorch.org/whl/cpu

# Run any script
python3 all_fixes.py
python3 fix_v3.py
# etc.
```

The scripts use `yfinance` to pull data and `torch` for the models. They run on CPU (no GPU needed).

## What these scripts do (summary)

The 8 scripts cover the 12 additions to the paper:
1. Pre-reg architecture search (Transformer wins)
2. Diebold-Mariano forecast comparison
3. Nested regressions
4. Information-theoretic analysis (MI)
5. Ablation study (K=1 to 5 cascade levels)
6. Rolling stability (24 windows, 2002-2024)
7. Bootstrap confidence intervals
8. FNO explainability
9. Strategy enhancement (vol-targeting + vol-timing)
10. New theorem D.1
11. Walk-forward validation
12. Per-region Transformer (intl)

## Earlier scripts (lost on sandbox reset)

The earlier scripts from the iterative-cycles session (cycle1, cycle2, cycle3, prereg_iter1, prereg_iter2, prereg_iter3, prereg_experiment, info_ablation_rolling, nested_regressions, new_theorem, dm_test, dm_test_full) were on previous workbench sandboxes that got reset. They are not recoverable from the workbench. They can be reconstructed from the existing result files in `results/` and the methodology described in the paper.