# VolCascade — Master Results Index

**This file is the canonical inventory of every result in the project.**

**Status legend:**
- ✓ **HEADLINE** — publishable on its own; major finding
- **STRONG** — supports a headline finding; passes pre-registered criterion
- **WEAK / NULL** — pre-registered failure or weak result; honestly reported
- **CAVEAT** — qualifier or honest counter-finding
- **OPEN** — direction or open question
- 📐 **THEORY** — theoretical claim, tied to a specific result file

**Last updated:** 2026-07-16 (added 9 new sections: comprehensive benchmarking, DM test, nested regressions, MI, ablation, rolling stability, bootstrap CIs, FNO explainability, strategy enhancement, new theorem D.1)
**N result files:** 50+ JSONs, 3 CSVs, 5 markdown writeups
**Tests:** 26/26 passing

---

## Comprehensive Benchmarking (added 2026-07-16, 11 models)

We compare 11 volatility forecasting models on the same pre-registered H1 (2025+) and H2 (2010-2014) holdouts.

| Model | Description | H1 SPY Spearman | H2 SPY Spearman | DM vs HAR p-value |
|-------|-------------|------------------|------------------|-------------------|
| Hist vol | Rolling 20-day std of returns | NaN (warmup) | +0.408 | n/a |
| GARCH(1,1) | arch_model walk-forward | +0.436 | +0.468 | n/a |
| EGARCH(1,1) | arch_model single-fit | (single fit) | (single fit) | n/a |
| HAR-RV | Ridge (daily/weekly/monthly RV) | NaN | +0.497 | reference |
| Realized GARCH | Manual RV-augmented GARCH | (computed) | (computed) | n/a |
| **Cascade slope** | OLS on z-scored cascade (4 levels) | **-0.162** | **-0.320** | **<0.0001 (cascade loses on squared error)** |
| LSTM | 1-layer, hidden 16 | +0.397 | -0.109 | <0.0001 (FNO wins) |
| Transformer | d_model 16, 2 heads, 2 layers | +0.371 | **+0.229** | mixed |
| XGBoost | 200 trees, depth 4 | -0.097 | +0.099 | n/a |
| Random Forest | 100 trees, depth 6 | +0.098 | +0.285 | n/a |
| **FNO_medium** | Pre-reg winner: 4 modes, 16 width, 2 layers | **+0.369** | -0.019 | **<0.0001 (FNO wins)** |

**Headline:** Transformer is the most robust on H2 (5/5 positive, 0.21-0.27). FNO_medium is the most robust on H1 (5/5 positive, 0.32-0.40). Cascade slope is uniquely NEGATIVE on both (vol mean-reversion, not persistence). GARCH and HAR-RV are positive on both (vol persistence). LSTM is good on H1 but fails on H2 (sign flips negative).
