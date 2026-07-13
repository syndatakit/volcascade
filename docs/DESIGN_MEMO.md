# Volatility Cascade — Design Memo

**Date:** 2026-07-13
**Authors:** Nitya Hapani (lead), pong (implementation)
**Repo:** https://github.com/Nityahapani/volcascade
**Target venue:** Modern Finance (DOAJ peer-reviewed, open access)

---

## Goal

Build a Python package + companion paper that defines the **volatility cascade** — a term structure of differentiation order for realized volatility — and uses it to classify regime breaks (H1), mark regime exits (H2), separate idiosyncratic from systemic risk via cross-sectional decoupling (H3), and test whether these dynamics hold in frontier markets (H4).

The paper's distinguishing contribution is the *shape-based, OHLCV-only, options-free* nature of the statistic and its *first-of-kind cross-market extension* to frontier/emerging markets.

---

## Locked decisions

### Methodology

| Decision | Choice | Rationale |
|---|---|---|
| **Cascade construction** | orders 1–4 of realized volatility, each z-scored against trailing history | Anchored by "vol is rough" literature (Gatheral et al. 2018) — orders beyond 4 become noise-dominated |
| **Lookback windows** | 60, 120, 252 trading days (robustness battery) | Captures day-of-week effects (Abdeldayem 2025) and VVIX asymmetry (Albers 2023) |
| **Cascade slope summary** | Linear regression slope of order index vs z-score (primary); entropy of cascade distribution (secondary) | Parsimonious + reviewable; entropy as non-linear robustness check |
| **H3 decoupling definition** | Chow test on joint distribution at each order k (primary); cross-correlation threshold (robustness) | Most defensible against "this is just smoothing" critique; multiple-testing concerns handled by BH-FDR |
| **Comparison battery** | RCM (Ang-Bekaert 2002b), Bai-Perron F-test, HMM (Gaussian 2-/3-state), MS-AR(1) (Hamilton 1989), Wasserstein k-means (Campani 2021), Inclán-Tiao CUSUM | Canonical set across the regime-detection literature |
| **Adversarial test** | Synthetic AR/GARCH series calibrated separately to DM and FM liquidity params; verify no spurious cascade steepening in either | Rebuts the "this is just vol-of-vol with extra steps" critique; the strongest piece of the paper |
| **Multiple testing** | Benjamini-Hochberg FDR across all tests (4 hypotheses × 2 samples × 3 lookbacks × 5 forward windows) | Preempts reviewer concerns; defines the unit of "significance" |
| **Sample size** | Effective N at each differentiation order reported explicitly for both universes; order-4 estimates in frontier are exploratory | Transparency about where the data carries information vs. where it doesn't |

### Pre-registered success criteria

| Hypothesis | Pass criterion |
|---|---|
| **H1** | Cascade-classified events → ≥ 2× larger forward 5-day drawdown than order-1-only classification |
| **H2** | Cascade-convergence exits → < 30% false exit rate, vs. ~50% for order-1 MA baseline |
| **H3** | Decoupling order predicts event type with AUC > 0.7 |
| **H4** | Classification accuracy differs significantly between DM and FM (p < 0.05 after BH-FDR) |

Defining these *now* prevents p-hacking and gives reviewers a clean pass/fail.

### Scope

- **Paper:** all 4 hypotheses, developed (S&P 500 constituents + SPDR sector ETFs) + frontier (6 country ETFs + constituents).
- **Package MVP (v0.1.0):** core cascade construction + H3 decoupling + 3 baselines (HMM, Wasserstein k-means, Inclán-Tiao CUSUM). Ships as soon as it's useful.
- **Package v1 (v0.2.0+):** Bai-Perron, RCM, additional decoupling methods, full viz suite.
- **Pilot sequence:** S&P 500 first (faster iteration), then frontier extension.

### Frontier sample (H4)

NSE Kenya, GSE Ghana, BVSP Brazil, JSE South Africa, NSE India, BSE Bangladesh — paired with the relevant country/regional ETF as the "sector" proxy in H3.

### H3 ground-truth event list

| Class | Sources | Examples |
|---|---|---|
| **Idiosyncratic** | Zacks earnings surprises, SDC M&A, BioPharmCatalyst FDA, CEO exits | Single-name earnings beats/misses, deal announcements, binary trial readouts |
| **Systemic** | FOMC, NFP, GFC peak days, COVID crash | Macro-policy events, broad-market shocks |

Built from public sources; curated table committed as `data/ground_truth_events.csv`.

### H3-primary vs H1-primary

Strategic call: **H1-primary, H3-differentiator.** H1 is the most intuitive entry point for reviewers; H3 is the most novel piece and stays in the spotlight as the differentiator. H4 is the cross-market distinguishing feature vs. existing vol-of-vol literature.

---

## Package design

**Name:** `volcascade` (locked to match repo)

**Modules:**

| Module | Responsibility |
|---|---|
| `volcascade.cascade` | Core cascade construction (orders 1–N, z-scoring, slope, entropy) |
| `volcascade.decoupling` | H3 decoupling tests (Chow, cross-correlation) |
| `volcascade.baselines` | Comparison battery (HMM, Wasserstein k-means, Inclán-Tiao CUSUM, Bai-Perron, RCM) |
| `volcascade.regime` | H1/H2 regime entry and exit detection |
| `volcascade.io` | yfinance data loaders + curated frontier sample |
| `volcascade.viz` | Cascade plots, slope heatmaps, regime overlays |

**API sketch:**

```python
import volcascade as vc

# Load data
prices = vc.io.load_prices(["SPY", "XLK", "XLF"], start="2010-01-01")

# Construct cascade
cascade = vc.cascade.build(prices, orders=[1, 2, 3, 4], lookback=120)

# Cascade slope (one number per t)
slope = vc.cascade.slope(cascade, method="linear")

# H3 decoupling for a stock-sector pair
decoupling = vc.decoupling.test(cascade["AAPL"], cascade["XLK"], method="chow")

# Run comparison battery
battery = vc.baselines.compare(cascade, prices, methods=["hmm", "wasserstein", "cusum"])

# Visualize
vc.viz.plot_cascade(cascade, slope)
```

---

## Deliverable sequence

| # | Deliverable | ETA (working days) | Status |
|---|---|---|---|
| 1 | Design memo (this doc) | today | **done** |
| 2 | Methodology doc (5–8 pages, math + pseudocode) | 3–4 days | pending |
| 3 | Package MVP (v0.1.0) — core cascade + decoupling + 3 baselines | 1–2 weeks | pending |
| 4 | S&P 500 pilot (all 4 H-tests + comparison battery) | ~1 week compute | pending |
| 5 | Package v0.1.0 → PyPI | when MVP done | pending |
| 6 | Paper section 3 draft (drop-in for paper) | ~1 week after pilot | pending |
| 7 | Frontier extension (H4) + paper section 4 | 2–3 weeks | pending |
| 8 | JOSS paper for the package | optional, after v1 | pending |

---

## Risk register

| Risk | Mitigation |
|---|---|
| Frontier data quality (Yahoo gaps, ticker deaths) | Curated CSV per market; manual fixup for known issues; fallback to FRED/RBI for indices |
| Order-4 vol is at the noise floor | Validate on synthetic AR/GARCH first; report effective N per order; treat order-4 frontier estimates as exploratory |
| H3 decoupling may not replicate on real data | Synthetic ground-truth test before claiming; cross-validate on multiple event types |
| Multicollinearity across orders inflates slope variance | VIF check; ridge-regularized slope as robustness; report both |
| Multiple testing inflates false discoveries | BH-FDR across all 120+ tests; pre-registered test battery |
| H4 cross-market difference may be confounded by liquidity proxy | Synthetic adversarial test (step 7 of brief) — the single most important piece of the paper |
| Reviewer pushback: "this is just vol-of-vol with extra steps" | Preempted by adversarial test + the OHLCV-only/no-options contribution + the cross-market extension |

---

## Division of labor

| Owner | Responsibilities |
|---|---|
| **Nitya** | Final say on methodology, paper writing voice, application narrative, H3 design calls, ground-truth event table |
| **pong** | Design memo, methodology doc, code (package + experiments), pilot, results, package release, section 3 draft |

Working in parallel with the ICAIF paper — this is "when I have time" not a deadline-driven push. The deliverable sequence above is in working days, not calendar days.

---

## Workflow

- **Direct commits to `main`, no PRs.** Local feature branches in sandbox for my own rollback safety; every `git push` lands on main.
- **Fine-grain GitHub token**, scoped to this repo only, used via env var, never committed.
- **Review cadence:** you review commits as they land. Every commit message describes what changed and why.

---

*End of design memo. Locked: 2026-07-13. Review and edit before methodology doc starts.*
