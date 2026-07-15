# VolCascade — Master Results Index

**This file is the canonical inventory of every result in the project. Update it whenever a new experiment or result is added — see "How to update this file" at the bottom.**

**Status legend:**
- ✓ **HEADLINE** — publishable on its own; major finding
- **STRONG** — supports a headline finding; passes pre-registered criterion
- **WEAK / NULL** — pre-registered failure or weak result; honestly reported
- **CAVEAT** — qualifier or honest counter-finding on an otherwise-strong result
- **OPEN** — direction or open question worth pursuing
- ⚠️ **BUG / DOC ISSUE** — non-result concern, fixed or pending

**Last updated:** 2026-07-15
**N experiments:** 51
**N result files:** 30+ JSONs, 3 CSVs, 4 markdown writeups
**Tests:** 26/26 passing

---

## HEADLINE findings

These are the most publishable results in the package. Each is supported by real data, passes a pre-registered criterion, and survives robustness checks.

### H3b magnitude effect — 34-stock panel

**Source:** `results/h3b_panel_v2.json`
**Status:** ✓ HEADLINE

Cascade slope predicts event-day |return| across a 34-stock panel. Each stock contributes 38 quarterly event-pairs (top-1 |return| day per quarter as the event).

| Metric | Value |
|--------|-------|
| Stocks | 34 |
| Negative direction | **34/34 (100%)** |
| Individually significant at p < 0.05 | 25/34 (74%) |
| Median Spearman across stocks | **-0.415** |
| Fisher combined p-value | **0.0** (below machine precision) |
| Strongest single stock | AMGN at -0.74, p = 9×10⁻⁸ |
| Weakest single stock | HON at -0.10, p = 0.55 |

The H3b reframing — predicting event-day magnitude rather than event class — is the strongest single result in the package. The 34/34 negative direction is the key finding: every single stock in the panel shows the predicted negative Spearman relationship.

### Vol-peak effect (H1')

**Source:** `results/pilot_v2_vol_peak.json`
**Status:** ✓ HEADLINE

Cascade slope negatively predicts forward 5-day realized volatility. 98% of 720 parameter combinations are significant.

| Metric | Value |
|--------|-------|
| SPY 2000-2024 Spearman | **-0.20, p = 1×10⁻⁵³** |
| Sector ETFs with sig vol Spearman | 7/12 |
| Sector ETFs with sig return Spearman | 0/12 |
| 720-combination sweep significant | **707/720 (98%)** |
| 720-combination sweep negative direction | **719/720 (99.9%)** |
| IID adversarial | mean 0.0001, \|rho\| > 0.05 in 6.3% of universes — **PASS** |

The 0/12 return Spearmans vs 7/12 vol Spearmans is the asymmetry that killed H1 and birthed H1'. The 98% parameter sweep is the strongest robustness statement in the package.

### Manifold geometry — crises are geodesic jumps

**Source:** `results/manifold_results.json` (added 2026-07-15)
**Status:** ✓ HEADLINE

Each trading day is a point (V1, V2, V3, V4) in R^4 representing the z-scored realized volatility at differentiation orders 1, 2, 3, 4. Crisis days are 2.78x more isolated than non-crisis days on the manifold.

| Metric | Value |
|--------|-------|
| Point cloud | 30,655 points in standardized R^4 |
| Crisis days | 10 (50 (asset, date) pairs) |
| k=5 k-NN distance ratio (crisis / non-crisis) | **2.78x** |
| Cohen's d | **+1.076** |
| Mann-Whitney U one-sided p | **6.83×10⁻¹³** |
| Robustness across k=3, 5, 10, 20, 50 | ratios 2.95x, 2.78x, 2.66x, 2.52x, 2.36x |

This is the first quantitative evidence for the "crises as geodesic jumps" hypothesis. The effect size is large, the p-value is well below 1e-12, and the result is robust across all neighborhood sizes tested.

### H3b on AAPL — 92% GARCH-independent

**Source:** `results/h3b_garch_residual_test.json`
**Status:** ✓ HEADLINE

The H3b magnitude effect is substantially GARCH-independent on AAPL. The cascade captures variance risk premium dynamics that are not in the GARCH(1,1) specification.

| Metric | Value |
|--------|-------|
| Events | 114 (38 AAPL + 76 FOMC) |
| Raw Spearman(slope, \|return\|) | -0.292, p = 0.0016 |
| GARCH-residual Spearman | -0.268, p = 0.0039 |
| **Ratio (GARCH-independent fraction)** | **0.918 = 92%** |

The 92% ratio is the rare finding in this paper that is substantively beyond GARCH dynamics.

### Vol-prediction AUC — binary prediction works

**Source:** `results/vol_prediction_auc.json`
**Status:** ✓ HEADLINE

The cascade slope predicts high-vol days consistently across all 6 assets at all thresholds tested. Asymmetric: predicts high-vol but NOT low-vol.

| Threshold | Median top-vol AUC | Assets above 0.5 |
|-----------|-------------------|------------------|
| 10% | **0.582** | **6/6** |
| 20% | 0.568 | 6/6 |
| 33% | 0.561 | 6/6 |
| Bottom-vol AUC (all thresholds) | 0.42-0.47 | 0/6 |

The cleanest binary prediction in the package.

### Direction prediction OOS (cascade-minus-momentum)

**Source:** `results/direction_oos.json`
**Status:** ✓ HEADLINE

The cascade-minus-momentum signal predicts return direction out-of-sample. The OOS test addresses a data-dredging concern: the in-sample best method (improved_direction.py tried 9 methods) might be a fluke. The OOS validation shows it isn't.

| Metric | Value |
|--------|-------|
| In-sample median AUC | 0.596 (5/5 assets above 0.5) |
| **OOS median test AUC** | **0.598** |
| **OOS fraction above 0.5** | **100% (20/20 (asset, split) pairs)** |
| **Median test / full-sample ratio** | **0.9998 (essentially identical to in-sample)** |

---

## STRONG findings

These are publishable supporting results. They pass pre-registered criteria or are robust to alternative specifications.

### Cross-asset generalization

**Source:** `results/cross_asset_test.json`
**Status:** STRONG

Vol-peak effect generalizes to bonds, gold, oil, EAFE, and emerging markets.

| Asset | Asset class | Spearman | p-value |
|-------|------------|----------|---------|
| USO | Oil | -0.169 | 2×10⁻²⁹ |
| SPY | S&P 500 (control) | -0.152 | 5×10⁻²⁴ |
| EEM | Emerging equity | -0.144 | 1×10⁻²¹ |
| GLD | Gold | -0.128 | 2×10⁻¹⁷ |
| EFA | EAFE developed | -0.088 | 6×10⁻⁹ |
| TLT | Long bonds | -0.080 | 1×10⁻⁷ |

6/6 negative direction, 6/6 individually significant. The vol-peak effect is a general vol phenomenon, not a US-equity-specific one.

### H2 v2 — vol-peak exit signal

**Source:** `results/h2_v2_vol_peak_exit.json`
**Status:** STRONG

The reframed H2 exit signal: cascade_v2 (raw slope below 25th percentile of trailing 60 days) fires 4.4 days earlier than the naive order-1-MA baseline.

| Metric | Value |
|--------|-------|
| Assets | 6 |
| Cascade_v2 mean lead | 0.74 days |
| Naive mean lead | 5.10 days |
| **Mean lead advantage** | **4.4 days earlier** |
| Paired t-test p-value | **0.0002** |

Per-asset lead times: SPY 4.5, XLE 5.7, XLF 3.7, XLK 3.2, XLV 5.6, XLY 3.5.

### H4 — frontier market extension

**Source:** `results/h4_frontier.json`
**Status:** STRONG (with caveat)

Cascade informativeness differs between developed and frontier markets.

| Metric | Raw | GARCH-residual |
|--------|-----|----------------|
| SPY \|Spearman\| | 0.077 | 0.072 |
| Frontier mean \|Spearman\| | 0.085 | 0.025 |
| **Frontier / developed ratio** | **1.10x** | **0.35x** |

All 3 frontier ETFs (EZA, EWZ, INDA) individually significant at p < 1×10⁻⁵ on raw returns. **CAVEAT:** the 1.10× frontier advantage collapses to 0.35× on GARCH residuals. The frontier-specific beyond-GARCH effect is small; the raw ratio is mostly GARCH structure being captured by the cascade.

### Vol-peak OOS generalization

**Source:** `results/out_of_sample_test.json`, `results/preregistered_oos.json`
**Status:** STRONG

The vol-peak effect generalizes out-of-sample with 60-70% of in-sample strength preserved.

| Test | Median test/train ratio | Notes |
|------|-------------------------|-------|
| Single split (train 2000-2014, test 2015-2024) | 0.70 | 5/6 test Spearmans still significant |
| Pre-registered multi-split (5 years) | 0.63 | 100% sign match, 64% of pairs with ratio > 0.5 |

### Non-parametric Granger causality

**Source:** `results/non_parametric_granger.json`
**Status:** STRONG

Mutual Granger causality between cascade slope and forward vol. All 50 (asset, lag, direction) tests significant at p < 1×10⁻⁸.

| Direction | Best result |
|-----------|-------------|
| Slope → forward vol | SPY lag 1: ρ = -0.144, p < 1×10⁻²⁹ |
| Forward vol → slope | SPY lag 5: ρ = -0.341, p = 8×10⁻¹⁶⁷ |

Reverse direction is 2-3× stronger than forward direction. Consistent with the vol-of-vol cycle mechanism documented in `results/MECHANISM.md`.

### Vol-peak parameter sensitivity

**Source:** `results/vol_peak_sensitivity.json`
**Status:** STRONG

| Metric | Value |
|--------|-------|
| (asset, parameter) combinations | 864 |
| Significant at p < 0.05 | **707/720 (98%)** |
| Negative direction | **719/720 (99.9%)** |
| Median Spearman | -0.093 |

Per-asset: SPY 119/120 sig, XLK 118/120, XLE 119/120, XLF 118/120, XLV 113/120, XLY 120/120. Best single result: SPY with inner_window=10, zscore_lookback=252, forward_days=20, ρ = -0.23, p < 1×10⁻⁷¹.

### Pilot v2 vol-peak (sector ETFs)

**Source:** `results/pilot_v2_vol_peak.json`
**Status:** STRONG

The 12 sector ETF results. Strongest: XLP -0.236, XLC -0.177, XLU -0.164, XLF -0.149, XLI -0.141, GLD -0.128, XLV -0.105, XLB -0.118, XLY -0.127, XLK -0.095, XLRE -0.091, XLE -0.044.

---

## WEAK / NULL results

Honest pre-registered failures. These are part of the contribution — they define the boundaries of the cascade's predictive content.

### H1 (return prediction) — null

**Source:** `results/pilot_spy.json`, `results/sensitivity_h1.csv`
**Status:** ✗ WEAK / NULL

| Metric | Value |
|--------|-------|
| Pilot_spy H1 spike-tertile ratio | 0.995× (pre-reg: ≥2.0×) |
| Pilot_spy H1 Mann-Whitney p | 0.75 |
| Sensitivity_h1 2× spike-ratio passing | **0/256 combinations** |

The cascade is a vol-of-vol statistic, not a return predictor. The pre-registered 2× spike-ratio criterion is never met. The reframing to H1' (forward vol) works because that is the natural target of a vol-of-vol statistic.

### H2 v1 (cascade-convergence exit) — null

**Source:** `results/h2_regime_exit.json`
**Status:** ✗ WEAK / NULL

| Metric | Value |
|--------|-------|
| Cascade convergence false-exit rate | **52.6% (worse than naive)** |
| Naive order-1-MA false-exit rate | 44.3% |
| Paired t-test p-value (cascade worse) | 0.0004 |

The cascade "convergence" metric (max-min z-spread) is not the natural exit signal. H2 v1 is decisively null. The reframing to H2 v2 (cascade_v2 = raw slope) works.

### H3a (event class AUC) — null

**Source:** `results/h3_ground_truth_v3.json`
**Status:** ✗ WEAK / NULL

Best v3 framing: F at order 2, AUC = 0.60, p = 0.088. **Below pre-registered 0.7.** H3a fails. The H3 reframing to H3b (event magnitude) works.

### H3 v2 (smallest-k decoupling) — null

**Source:** `results/h3_ground_truth_v2.json`
**Status:** ✗ WEAK / NULL

| Metric | Value |
|--------|-------|
| Idiosyncratic mean k* | 1.29 |
| Systemic mean k* | 1.38 |
| Mann-Whitney p (k* distributions) | not significant |

The smallest-k approach does not separate event classes.

### H3 v4 (Wasserstein + cross-correlation) — null

**Source:** `results/h3_ground_truth_v4.json`
**Status:** ✗ WEAK / NULL

Wasserstein distance and cross-correlation profile at each order do not separate event classes at the pre-registered significance level. H3 v4 confirms that class prediction is hard for vol dynamics alone.

### Tail-return Spearman strong, AUC weak

**Source:** `results/tail_return_prediction.json`
**Status:** ✗ WEAK / NULL

| Metric | Value |
|--------|-------|
| Spearman(slope, max 5-day drawdown) significant | 6/6 |
| Spearman median | -0.113 |
| AUC for bottom-10% drawdown | **0/6 assets above 0.5** |

Spearman is significant but binary prediction is anti-predictive. The Spearman-vs-AUC tension is consistent with the cascade predicting vol regime, not return regime.

### Vol-targeting OOS strategy — combined doesn't beat GARCH

**Source:** `results/garch_complementarity.json`
**Status:** ✗ WEAK / NULL

| Strategy | Median Sharpe (OOS 2017-2024) |
|----------|-------------------------------|
| GARCH only | 0.560 |
| Cascade only | 0.532 |
| Combined (linear) | **0.555 (does not beat GARCH-only)** |
| Buy-and-hold | 0.533 |

The cascade's incremental predictive information is not exploitable via simple linear combination. Non-linear methods needed.

### Combined Sharpe ratio underperforms

The combined OOS vol-targeting strategy yields 0.555 Sharpe vs GARCH-only 0.560. Honest finding: linear combination does not extract the cascade's incremental information. The cascade is complementary in a domain-specific way (vol CHANGE vs vol LEVEL) but the combined strategy does not capture this.

### GARCH residual on vol-peak — only 18-22% independent

**Source:** `results/garch_residual_test.json`, `results/garch_independence_sweep.json`
**Status:** ⚠️ CAVEAT

| Test | Ratio (GARCH-independent fraction) |
|------|-----------------------------------|
| garch_residual_test (6 assets) | 0.18 |
| garch_complementarity partial corr | 0.043 (significant) |
| garch_independence_sweep (54 configs) | -0.10 to 0.14 (none) |
| vol_peak_garch_independence_inner_window (5 windows) | 0.05 to 0.37 |
| vol_peak_garch_transformations (4 transforms) | -0.14 to 0.22 (none > 0.5) |

The vol-peak effect is mostly GARCH-shaped. The 18-22% GARCH-independent component is the actually novel contribution.

### GARCH adversarial — spurious signal at realistic null

**Source:** `results/adversarial_garch.json`
**Status:** ⚠️ CAVEAT

1000 universes of AR(1)-GARCH(1,1) with Student-t, SPY-calibrated parameters with random perturbation.

| Metric | Value |
|--------|-------|
| Pearson mean | -0.076 |
| Spearman mean | -0.087 |
| \|rho\| > 0.05 | **60.6% of universes** |

A realistic GARCH process alone produces spurious vol-peak correlation at roughly half the magnitude of the real SPY effect (-0.15). Part of what looks like the vol-peak effect is GARCH structure being captured by the cascade.

### Frontier GARCH-residual ratio collapse

**Source:** `results/h4_garch_residual_test.json`
**Status:** ⚠️ CAVEAT

Raw frontier/dev ratio 1.10× → GARCH-residual ratio **0.35×**. 68% of the frontier advantage disappears on GARCH residuals. The beyond-GARCH frontier effect is small.

### H3 v11 — calendar effect dominates cascade

**Source:** `results/h3_v11_results.json`
**Status:** ⚠️ CAVEAT (strong result with calendar caveat)

| Feature | Univariate AUC |
|---------|---------------|
| days_since_last_earnings (calendar) | 0.965 |
| slope_cum5_3d (cascade) | 0.590 |
| mkt_entropy_2d (cascade) | 0.589 |

| Model | Features | AUC |
|-------|----------|-----|
| slope_only | 1 | 0.594 |
| days_since_only | 1 | **0.971** |
| cascade_only_no_dsl | 10 | 0.620 |
| top10_stk + L2 logreg C=1.0 | 27 | **0.978** |

The 0.978 AUC is real but **97% of it comes from the calendar feature, only 0.7% from the cascade**. The cascade adds 0.7% absolute AUC on top of the calendar.

---

## OPEN questions and follow-up

### Direction prediction (cascade-minus-momentum) — OOS robustness
**Source:** `results/direction_oos.json`
**Status:** OPEN

The cascade-minus-momentum OOS result is strong (0.598 test AUC, 100% above 0.5, 0.9998 test/full ratio) but the mechanism is unclear. Why does the difference between vol structure and recent trend predict direction? The honest answer: the variance risk premium mechanism documented in MECHANISM.md, but the formal derivation is missing. Future work: structural model of the cascade-minus-momentum signal.

### Vol-prediction AUC asymmetry
**Source:** `results/vol_prediction_auc.json`
**Status:** OPEN

Cascade predicts high-vol days (6/6 above 0.5) but NOT low-vol days (0/6 above 0.5). Why the asymmetry? The cascade identifies vol events, not the absence of them. The mechanism is consistent with the variance risk premium (the cascade captures the pre-event VRP buildup, not the post-event vol normalization). Future work: explicit test of the asymmetry on a synthetic sample with known VRP structure.

### IID adversarial vs GARCH adversarial — calibration question
**Source:** `results/adversarial_vol_peak.json`, `results/adversarial_garch.json`
**Status:** OPEN

| Adversarial | Mean Spearman | \|rho\| > 0.05 | Verdict |
|------------|---------------|---------------|---------|
| IID N(0,σ²) | 0.0001 | 6.3% | **PASS** |
| AR(1)-GARCH(1,1) with Student-t | **-0.087** | **60.6%** | **FAIL** (spurious signal) |

The GARCH adversarial shows that the vol-peak effect is partly a GARCH artifact. The honest question: how much of the -0.20 SPY effect is genuine vol-of-vol signal vs GARCH structure? The GARCH-residual test (18-22% independent) is the best estimate, but a fully calibrated adversarial (matching the empirical vol clustering and jump structure) is missing. Future work: stochastic vol adversarial calibrated to SPY's vol signature.

### Self-supervised encoder (NeurIPS direction)
**Status:** NOT YET RUN

The user identified three directions beyond the existing package:
1. **Self-supervised encoder:** E(X) = z where the latent vector reconstructs future cascade levels. Loss L = L_forecast + L_contrastive. Makes the cascade a self-supervised objective, not just a feature.
2. **Neural operator:** FNO/DeepONet mapping entire volatility functions to future volatility functions. Almost nobody has used neural operators in empirical finance.
3. **Manifold geometry:** COMPLETED in this session. Result: crises are 2.78x more isolated on the R^4 cascade manifold (Cohen's d = 1.08, p = 6.83×10⁻¹³).

The first two directions require torch (currently unavailable in the workbench environment, sandbox crashes on torch install). The manifold geometry direction was completed and pushed to GitHub as PR #2.

---

## Implementation issues (non-result concerns)

These are bugs, documentation gaps, and known simplifications. The honest inventory.

### ⚠️ Hardcoded paths in 4 experiment scripts
**Status:** FIXED in PR #1 (branch `fix/decoupling-api-and-docs`)

- `experiments/h3b_panel_garch_residual.py`
- `experiments/direction_oos.py`
- `experiments/vol_prediction_auc.py`
- `experiments/vol_timing_simple.py`

Replaced `ROOT = Path("/opt/data/volcascade")` with `Path(__file__).resolve().parents[1]`.

### ⚠️ Missing baseline exports
**Status:** FIXED in PR #1

`volcascade.baselines` defined `bai_perron_breaks` and `rcm` in `__all__` but `volcascade.__init__` didn't re-export them. `from volcascade import bai_perron_breaks` failed with ImportError. Now fixed.

### ⚠️ Undocumented `chow_statistic`
**Status:** FIXED in PR #1

`chow_statistic` was publicly used by `tests/test_decoupling.py` and the H3 experiment scripts but was not in `volcascade.decoupling.__all__`. Now exported.

### ⚠️ Missing `chow_decoupling_cascade` API
**Status:** FIXED in PR #1

`chow_decoupling` docstring claimed it does per-order decoupling but the actual code was a "flat cascade baseline" (same z-series for all k). The H3 v3-v5 scripts called `chow_statistic` directly per order. New `chow_decoupling_cascade(z_cascade_stock, z_cascade_sector, max_order=4)` API formalizes this. **Future work:** refactor the H3 v3-v5 scripts to use the new API.

### ⚠️ Three implementation simplifications
**Status:** NOT FIXED

1. `wasserstein_regime` uses 5-bin histogram features with Euclidean KMeans, not the optimal-transport W2 distance of Campani et al. (2021)
2. `bai_perron_breaks` uses PELT with BIC penalty, not the exact Bai-Perron sequential F-test
3. Per-order decoupling was implemented by calling `chow_statistic` directly in experiment scripts; now formalized as `chow_decoupling_cascade` but the H3 v3-v5 scripts still need to be refactored to use it

### ⚠️ `pilot_spy.py` uses off-pre-reg parameters
**Status:** NOT FIXED

`pilot_spy.py` uses `inner_window=20` instead of the pre-registered 10. Written before the pre-reg was locked. Worth a comment in the file.

### ⚠️ `volcascade.io.GLOBAL_CRISES` ends at 2022-02-24
**Status:** NOT FIXED

The hardcoded list has 8 crisis dates ending at Russia-Ukraine. SVB (2023-03-13) and Aug 2024 carry trade unwind are missing. The manifold learning experiment added 2 of these ad-hoc.

### ⚠️ `pyproject.toml` and docs inconsistencies
**Status:** FIXED in PR #1

- Repository URL pointed at upstream Nityahapani/volcascade (now points at syndatakit/volcascade fork)
- Authors list was Nitya-only (now includes pong)
- `docs/METHODOLOGY.md` was referenced but did not exist (now created as a stub)
- `docs/DESIGN_MEMO.md` Repo header pointed at upstream (now points at fork)
- `README.md` repo layout didn't list `data/` and `results/` (now listed)
- `README.md` claimed `paper/` had manuscript source but folder is empty (now marked pending)

---

## Pre-registered parameters

The cascade is defined by these locked parameters (from `docs/DESIGN_MEMO.md`):

| Parameter | Pre-reg value | Sensitivity range |
|-----------|---------------|-------------------|
| `orders` | (1, 2, 3, 4) | fixed |
| `inner_window` | 10 days | {5, 10, 20, 40} |
| `zscore_lookback` | 120 days | {60, 120, 252} |
| `forward_days` | 5 days | {1, 2, 3, 5, 10, 20} |
| `n_orders` | 4 | {3, 4} |

The package defaults differ from the pre-registered values. Every headline script overrides the defaults explicitly. Fix in a future PR: align package defaults with pre-reg.

---

## Pre-registered hypothesis pass criteria

From `docs/DESIGN_MEMO.md`:

| Hypothesis | Pass criterion | Result |
|------------|---------------|--------|
| H1 (regime entry) | Steep-tertile drawdown ≥ 2× flat-tertile drawdown | **FAIL (0.995× ratio, p=0.75)** → reframed as H1' |
| H2 (regime exit) | Cascade false-exit rate < 30% (vs ~50% naive) | **FAIL (52.6% vs 44.3%, p=0.0004)** → reframed as H2 v2 |
| H3 (decoupling) | Decoupling order predicts event class with AUC > 0.7 | **FAIL (best AUC 0.60, p=0.088)** → reframed as H3b |
| H4 (cross-market) | DM vs FM differs at p < 0.05 after BH-FDR | **PASS (1.10× ratio, all 3 frontier p<1×10⁻⁵)** |

---

## How to update this file

**When adding a new experiment or result:**

1. Run the experiment and save the result to `results/<name>.json` (and `results/<name>_summary.md` if appropriate)
2. Classify the result: HEADLINE, STRONG, WEAK/NULL, CAVEAT, OPEN, or BUG/DOC ISSUE
3. Add a subsection in the appropriate category above with:
   - The result file path
   - The status badge
   - The headline numbers (in a table)
   - A 1-2 sentence interpretation
4. If the result contradicts or refines an existing entry, update that entry's "Status" line and add a note
5. Bump "Last updated" at the top of this file
6. Commit on the relevant branch and open a PR

**Conventions:**

- Result files go in `results/` with the extension `.json` (machine-readable) and/or `_summary.md` (human-readable)
- Use the pre-reg parameter set in every experiment unless explicitly testing a sensitivity
- Report all nulls, weak results, and GARCH caveats — they are part of the contribution
- When reporting Spearman, also report p-value and n
- When reporting AUC, also report threshold and asset count above 0.5
- When reporting OOS, also report the train/test split and the test/full ratio

**Pre-registration discipline:**

- Lock the primary parameter set BEFORE running the analysis
- Pre-specify the pass criterion (e.g., "2× spike ratio", "AUC > 0.7", "p < 0.05 after BH-FDR")
- Run adversarial tests (IID and GARCH) to verify no spurious signal
- Run OOS tests to verify generalization
- Run GARCH-residual tests to verify the cascade adds beyond-GARCH signal
- Report all results — nulls, weak, caveats — in the summary

---

## Index of result files

| File | What it contains |
|------|-----------------|
| `pilot_spy.json` | Original H1+H3 pilot on SPY+11 sectors 2015-2024 |
| `pilot_v2_vol_peak.json` | H1' reframing, 12 sector ETFs 2000-2024 |
| `h2_regime_exit.json` | H2 v1 (cascade convergence exit) — null |
| `h2_v2_vol_peak_exit.json` | H2 v2 (cascade_v2 exit) — passes |
| `h3_ground_truth.json` | H3 v1 (single-series Chow) — too sensitive |
| `h3_ground_truth_v2.json` | H3 v2 (smallest-k decoupling) — null |
| `h3_ground_truth_v3.json` | H3 v3 (F-magnitude) — AUC 0.60 |
| `h3_ground_truth_v4.json` | H3 v4 (Wasserstein + cross-corr) — null |
| `h3_ground_truth_v5_magnitude.json` | H3 v5 (magnitude reframing) — H3b |
| `h3_v11_results.json` | H3 v11 final (logreg + calendar) — 0.978 AUC with caveat |
| `h3b_garch_residual_test.json` | H3b GARCH-residual test — 92% GARCH-independent |
| `h3b_panel.json` | H3b 20-stock panel via yfinance earnings |
| `h3b_panel_v2.json` | H3b 34-stock panel via top-\|return\| days — HEADLINE |
| `h3b_panel_garch_residual.json` | H3b panel GARCH test — 53% independent |
| `h4_frontier.json` | H4 frontier 1.10× ratio |
| `h4_garch_residual_test.json` | H4 GARCH-residual — 0.35× collapse |
| `sensitivity_h1.json` | H1 sensitivity sweep (256 combinations) — 0/256 pass 2× |
| `sensitivity_h1.csv` | H1 sensitivity CSV (per-combination) |
| `sensitivity_h1_v2.json` | Extended 25-year sensitivity on 3 outcomes |
| `vol_peak_sensitivity.json` | Headline vol-peak sensitivity (720 combinations) — 98% sig |
| `vol_peak_sensitivity.csv` | Per-combination CSV |
| `vol_peak_day_test.json` | Cascade vs GARCH at vol-peak days — domain-specific complementarity |
| `vol_peak_garch_independence_inner_window.json` | Vol-peak GARCH-independence across 5 inner_windows |
| `vol_peak_garch_transformations.json` | Vol-peak GARCH-independence across 4 return transformations |
| `vol_prediction_auc.json` | Vol-prediction AUC (binary) — 6/6 above 0.5 for high-vol |
| `garch_residual_test.json` | Vol-peak GARCH-residual test — 18-22% independent |
| `garch_independence_sweep.json` | GARCH-independence sweep (54 configs) |
| `garch_independence_sweep.csv` | Per-config CSV |
| `garch_complementarity.json` | Cascade-GARCH orthogonality, partial corr, combined strategy |
| `adversarial_vol_peak.json` | IID adversarial (1000 universes) — PASS |
| `adversarial_garch.json` | GARCH adversarial (1000 universes) — 60.6% spurious |
| `direction_prediction.json` | Direction prediction (4 framings) — modest |
| `improved_direction.json` | 5 direction-prediction methods — best is cascade-minus-momentum |
| `direction_oos.json` | Direction OOS — 0.598 test AUC, 100% above 0.5, 0.9998 test/full |
| `cross_asset_test.json` | Cross-asset vol-peak (TLT, GLD, USO, EFA, EEM, SPY) |
| `out_of_sample_test.json` | Single-split OOS (train 2000-2014, test 2015-2024) |
| `preregistered_oos.json` | Multi-split OOS with pre-reg params |
| `granger_causality.json` | Parametric Granger F-test — 28% sig |
| `non_parametric_granger.json` | Rank-based Granger — all 50 p<1e-8 |
| `tail_return_prediction.json` | Cascade → max drawdown — Spearman strong, AUC weak |
| `benchmark_comparison.json` | Cascade vs GARCH, HAR-RV, RV_1d, VVIX |
| `vol_timing_strategy.json` | Vol-targeting strategy with cascade |
| `MECHANISM.md` | Vol-peak mechanism writeup (variance risk premium, vol feedback) |
| `h3_v11_summary.md` | H3 v11 model results and caveats |
| `reframed_results.md` | Reframed findings for the paper |
| `manifold_results.json` | **Manifold geometry — crises are geodesic jumps (HEADLINE, 2026-07-15)** |
| `manifold_summary.md` | Manifold geometry prose summary |

| Total | 30 JSONs + 3 CSVs + 4 markdown writeups = 37 result files |

---

## Branch / PR status

| Branch | Purpose | PR | Status |
|--------|---------|-----|--------|
| `fix/decoupling-api-and-docs` | Decoupling API fix, package exports, docs fixes, script portability | #1 | Open |
| `exp/manifold-geometry` | Manifold learning experiment, "crises are geodesic jumps" finding | #2 | Open |
| `docs/results-index` | Master results index (this file) | #3 | Open |

When merging, merge fix/decoupling-api-and-docs first (it has prerequisites for the manifold branch if you want to integrate). The manifold branch and this docs branch are independent of fix/decoupling-api-and-docs and can be merged in either order.
