# Volatility Cascade — Implementation Notes

**Purpose:** document the known gaps between what the methodology and design
memo describe, and what the code currently does. This is the single place
where doc-vs-code drift is recorded so reviewers (and future-us) can see
the deltas at a glance.

**Maintained by:** pong. **Last audit:** 2026-07-14.

These are *not* bugs in the sense of "the code is broken" - everything in
`src/volcascade/` passes its 26-test pytest suite. These are simplifications
the implementation made to ship the pilot, plus a few honest method-vs-code
mismatches that the code/docs have been quietly carrying.

---

## 1. H3 decoupling: per-order test not implemented (TOP PRIORITY)

**Methodology says** (Section 6): for a stock-sector pair, the decoupling
order $k^*$ is "the smallest $k$ at which the joint distribution of
$(z^{(k)}_{i,t}, z^{(k)}_{b,t})$ rejects the null of equal conditional
distributions via a Chow test." This is a *per-order* test: the Chow
statistic must be computed on $z^{(1)}$, then on $z^{(2)}$, then on $z^{(3)}$,
then on $z^{(4)}$ - and $k^*$ is the smallest $k$ where any sliding window
rejects.

**Code does** (`src/volcascade/decoupling.py`): the `chow_decoupling()`
function takes two single-order series and loops $k = 1 \dots 4$, but
passes the *same* two series to `chow_statistic` at every $k$. The function's
own docstring admits this: *"In the current implementation, `z_stock` and
`z_sector` are treated as already-z-scored single-order series (the same
series across all k - i.e. a flat cascade)."* The result is a "flat cascade"
baseline that asks whether the stock-sector relationship has a structural
break in *any* window, but not at *which cascade order*.

**Workaround the experiments use:** the H3 v3-v5 experiment scripts
(`experiments/h3_ground_truth.py` and its `v3`/`v4`/`v5` variants) get the
per-order F-statistics by calling `chow_statistic` directly inside the
experiment, with the order-specific $z^{(k)}$ series passed in. This is
not exposed through the package API. The H3 v3-v5 result files in
`results/h3_ground_truth_v3.json`, `h3_ground_truth_v4.json`, and
`h3_ground_truth_v5_magnitude.json` were produced this way.

**Impact:** the headline H3 v3-v5 results (per-order F-statistics, the
event-magnitude Spearman of -0.11 across 6 assets) are computed correctly,
but they bypass the package API. The H3 v1-v2 results that use
`chow_decoupling()` directly (e.g. `results/h3b_garch_residual_test.json`)
are testing only the flat-cascade baseline, not the per-order claim.

**Fix priority:** **high**. Add a `decoupling_per_order(zcascade_stock,
zcascade_sector, max_order=4, lookback=252)` API that takes the *full
cascade dict* (orders 1..4 z-scored series) and runs `chow_statistic` once
per order. Replace the H3 v3-v5 inline calls with this API.

---

## 2. Baseline simplifications (MEDIUM PRIORITY)

### 2.1 Wasserstein k-means - actually Euclidean on histograms

**Code** (`src/volcascade/baselines.py::wasserstein_regime`):

```python
bins = np.linspace(np.nanmin(x), np.nanmax(x), 6)
feats = []
for i in range(window, len(x) + 1):
    hist, _ = np.histogram(x[i-window:i], bins=bins, density=True)
    feats.append(hist)
feats = np.asarray(feats)
km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
```

This is Euclidean KMeans on 5-bin histograms, **not** Wasserstein-2
distance. The Campani et al. 2021 reference is for optimal-transport
clustering in Wasserstein-2 space.

**Fix:** use `ot` (Python Optimal Transport) or `scipy.stats.wasserstein_distance`
to compute true Wasserstein distances between window-distributions, then
cluster via $k$-means in the resulting metric space (or via a Wasserstein
$k$-means algorithm). The current Euclidean implementation should be kept
as `wasserstein_regime_euclidean` for robustness comparison.

### 2.2 Bai-Perron F-test - actually PELT

**Code** (`src/volcascade/baselines.py::bai_perron_breaks`):

```python
from ruptures import Pelt
model = Pelt(model="rbf").fit(x.reshape(-1, 1))
pen = np.log(n) * np.var(x)
bkps = model.predict(pen=pen)
```

This is `ruptures.Pelt` with an RBF kernel, **not** Bai & Perron's
sequential F-test. The function returns change-point locations but no
F-statistics or significance values, so the "Bai-Perron F-test" claim in
the methodology is not actually testable against this function's output.

**Fix:** either (a) implement Bai-Perron's dynamic programming algorithm
(`statsmodels.tsa.stattools.breakpoints_hansen` or roll-our-own), returning
F-stats for the sequential test, or (b) rename the function to
`pelt_breaks` and update the methodology to reflect that PELT (not BP) is
the change-point baseline.

### 2.3 Inclán-Tiao CUSUM - finite-$n$ correction is a no-op

**Code** (`src/volcascade/baselines.py::cusum_regime`):

```python
a = 1.36 if significance == 0.10 else 1.63 if significance == 0.05 else 1.95
critical = a + (a - 0.4) * 0.0  # asymptotic; could refine for finite n
```

The `(a - 0.4) * 0.0` term is always zero. The `0.0` is a placeholder.
The asymptotic critical values are used at all sample sizes, which is
conservative for small $n$ but not by design.

**Fix:** use a simulation-based critical value (10,000 simulated Brownian
bridges at the actual $n$) or one of the published finite-$n$ refinements
(Kiefer, 1959; Butler, 1982). Either way, drop the `(a - 0.4) * 0.0` line
or make it actually compute something.

### 2.4 RCM - degenerate with hard labels

**Code** (`src/volcascade/baselines.py::rcm`):

```python
if states.ndim == 2:
    p = states.max(axis=1)
else:
    p = (states == np.bincount(states).argmax()).astype(float)
return float(400.0 * np.mean(p * (1.0 - p)))
```

With hard state labels (1-D `states`), $p \in \{0, 1\}$ makes
$p(1-p) = 0$, so RCM = 0. This is degenerate. The Ang-Bekaert formula
expects soft state probabilities.

**Fix:** either (a) enforce soft probabilities at the API level (raise
`ValueError` on 1-D hard labels with a message pointing users to
`hmm_regime` for soft probs), or (b) compute RCM correctly under the
hard-label assumption (e.g., $p_t = \mathbf{1}[s_t = \text{modal state}]$
yields RCM = 0, which is uninformative - just document this).

---

## 3. Frontier data layer: 4 of 6 markets are self-comparisons (HIGH PRIORITY)

**Code** (`src/volcascade/io.py::FRONTIER_SAMPLE`):

```python
FRONTIER_SAMPLE: dict[str, dict[str, str]] = {
    "NSE_KE": {"country_etf": "EZA", "sector_proxy": "EZA", "currency": "USD"},
    "GSE_GH": {"country_etf": "EZA", "sector_proxy": "EZA", "currency": "USD"},
    "BVSP":   {"country_etf": "EWZ", "sector_proxy": "EWZ", "currency": "USD"},
    "JSE":    {"country_etf": "EZA", "sector_proxy": "EZA", "currency": "USD"},
    "NSE_IN": {"country_etf": "INDA", "sector_proxy": "INDA", "currency": "USD"},
    "BSE_BD": {"country_etf": "XBS", "sector_proxy": "XBS", "currency": "USD"},
}
```

4 of 6 frontier entries have `country_etf == sector_proxy`. The H3
decoupling test on these entries is comparing a series to itself (or its
exact same country ETF, which is the same series). The H4 frontier results
in `results/h4_frontier.json` use the country_etf-to-country_etf comparison
implicitly, which is meaningless for the H3 decoupling claim.

**Fix:** for each frontier market, pair with an actual *sector* or
*regional* ETF that is **not** the country ETF. For example:
- NSE_KE: pair with `AFK` (Africa) or sector-specific ETFs
- BVSP: pair with `EWZ` (Brazil) vs `ILF` (Latin America) for cross-decoupling
- NSE_IN: pair with `INDA` (India) vs `EPI` (India earnings weighted) or
  sector-specific (e.g., `INXX` for infrastructure)

This is a real data-layer issue. Until fixed, the H4 "frontier decoupling"
results should be read as "the cascade signal is present in frontier
country-level ETFs," not "the cascade detects decoupling within frontier
markets."

---

## 4. Ground truth event table - coverage is partial (MEDIUM PRIORITY)

**Methodology says** (Section 6 ground-truth list): "idiosyncratic =
earnings surprises (Zacks), M&A announcements (SDC), FDA binary events
(BioPharmCatalyst), CEO exits; systemic = FOMC decisions, NFP releases,
GFC peak days, COVID crash days."

**Code does** (`experiments/h3_ground_truth.py`):
- `aapl_earnings_dates()`: 40 AAPL earnings events, 2015-2024
- `fomc_dates()`: 81 FOMC decision dates, 2015-2024
- **NFP releases:** not implemented (mentioned in the file docstring but
  no `nfp_dates()` function exists)
- M&A, FDA binaries, CEO exits: not implemented
- GFC peak days, COVID crash days: not implemented as a separate function

**Canonical CSV:** `data/ground_truth_events.csv` (added 2026-07-14, 121
events: 40 AAPL + 81 FOMC). This is now the single source of truth; the
inlined `aapl_earnings_dates()` and `fomc_dates()` functions in
`experiments/h3_ground_truth.py` should be replaced with a CSV loader.

**Fix:** (a) add `nfp_dates()` (120 events, first Friday of each month,
2015-2024 - skip BLS release calendar lookup for the v1), (b) add the
GFC peak dates (2008-10-09, 2008-09-15) and COVID peak (2020-03-16,
2020-03-23) as one-off systemic events, (c) consider adding M&A and FDA
events for v2. For v1, the AAPL+FOMC table is sufficient but reviewers
will note the asymmetry (40 idiosyncratic vs 81 systemic).

---

## 5. Test and methodology gaps (LOWER PRIORITY BUT EASY)

### 5.1 No tests for `viz.py` and `io.py`

`tests/` covers cascade, decoupling, and baselines. The viz module
(`plot_cascade`, `plot_slope`, `plot_regime_overlay`) and the io module
(`load_prices`, `load_returns`, `FRONTIER_SAMPLE`, `GLOBAL_CRISES`) have
zero direct test coverage. The yfinance data layer in particular is
fragile and untested.

**Fix:** add `tests/test_viz.py` (smoke tests for figure generation) and
`tests/test_io.py` (test `FRONTIER_SAMPLE` structure, test that
`GLOBAL_CRISES` parses cleanly, mock `yfinance.download` for
`load_prices`).

### 5.2 No integration / end-to-end test

The unit tests verify individual functions. There is no test that runs
the full pipeline (`load_prices` -> `build` -> `zscore` -> `slope` ->
export) on a small real dataset. Such a test would catch API drift
between modules and is the kind of test CI runs first.

**Fix:** add `tests/test_pipeline.py` that uses a 1-year window of SPY
data (cached as parquet, not pulled live) and verifies the cascade slope
is finite and has the expected sign on a known crash day.

### 5.3 No CI configuration

There is no `.github/workflows/` directory. Tests are not run on push.
This is the easiest item on this list to fix.

**Fix:** add `.github/workflows/ci.yml` running `pytest -v` on Python
3.10, 3.11, 3.12. Add a separate workflow for `ruff` lint and `mypy`
type checking.

### 5.4 Variance decomposition for the GARCH complementarity

`results/MECHANISM.md` Section 2.4 reports "78% GARCH-explained, 22% beyond
GARCH" as a partial-correlation ratio, not a formal variance decomposition.
Reviewers will want the latter.

**Fix:** compute a Shapley-value-based or Sobol-based decomposition of the
cascade slope + GARCH + momentum feature set on forward 5-day vol. This is
a 1-day computation, but the result needs to be written up carefully.

### 5.5 Multiple-testing correction is not applied

The methodology pre-registered BH-FDR across the full test battery
(4 H × 2 samples × 3 lookbacks × 5 forward windows = 120 tests). The
result JSONs in `results/` report raw p-values and `n_significant / n_total`
counts without FDR correction.

**Fix:** apply `statsmodels.stats.multitest.multipletests(method='fdr_bh')`
to every p-value in every results JSON, recompute significance, and
re-state the headline claims with the corrected counts.

### 5.6 `inner_window` inconsistency

The cascade default is 20 trading days (DESIGN_MEMO says "one trading
month"). The H3 v5 experiment uses 10. The `h1_forward_drawdown` test in
`pilot_spy.py` uses 60-day z-scoring (not 252). These are not
inconsistencies in the sense of bugs, but the results across experiments
are not directly comparable until a canonical `inner_window` and
`zscore_lookback` are picked and applied.

**Fix:** document the canonical value in METHODOLOGY §2 (probably 20) and
add a sensitivity battery in the appendix.

### 5.7 H2 v2 walk-forward validation

The H2 v2 result (cascade slope fires 4.4 days earlier than the naive
order-1 MA baseline, paired t-test $p = 0.0002$) is reported on the
in-sample data. The v2 metric was found by trying multiple summary
statistics (spread was tried first, failed; slope worked). Without
walk-forward validation, the 4.4-day lead could be an in-sample artifact.

**Fix:** redo H2 v2 with strict time-series CV (train on 2010-2015, test
on 2016-2020, etc.) and report the out-of-sample lead-time improvement.

---

## 6. Doc-vs-code references that have been fixed (2026-07-14)

This audit also fixed several stale references in the existing docs:

- **README.md** "Repo layout" no longer claims a `paper/` directory
  exists. The `paper/` manuscript source is still pending (see
  DESIGN_MEMO deliverable sequence).
- **README.md** no longer claims `volcascade.regime` is in the package;
  the H1/H2 logic is acknowledged to live in `experiments/`.
- **docs/METHODOLOGY.md** Section 6 now has a code-status callout
  pointing to this document.
- **docs/METHODOLOGY.md** Section 8 baseline table now flags the four
  simplifications above (Wasserstein, Bai-Perron, CUSUM, RCM).
- **docs/DESIGN_MEMO.md** modules table now has Status columns
  (shipped / pending / shipped-as-simplification).
- **results/MECHANISM.md** Section 2.4 now opens with a caveat on the
  "78% GARCH-explained" framing.
- **`data/ground_truth_events.csv`** is now the canonical event table;
  the inline `aapl_earnings_dates()` and `fomc_dates()` functions in
  `experiments/h3_ground_truth.py` should be replaced with a CSV loader
  in a follow-up commit.

---

*This is a living document. Update it whenever you find another gap, and
re-run the doc-vs-code audit at the start of each major refactor.*
