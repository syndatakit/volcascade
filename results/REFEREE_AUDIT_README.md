# Referee concern audit and consistency-rate simulation

**Date:** 2026-07-18
**Author:** Nitya Hapani & pong

## What this is

Two audits responding to specific reviewer concerns about the VolCascade paper:

### Audit 1: Referee concern audit (6 sub-tests)

Tests 6 robustness checks called out by the reviewer:

1. **Forecast-encompassing by horizon** (h = 1, 2, 3, 5, 10, 20) for both z1 and cs.
2. **Rolling z1 encompassing** (184 windows, 10 assets) for coefficient stability.
3. **VIF diagnostics** between cascade levels and HAR/GARCH regressors.
4. **Out-of-sample nested R^2** (M1=HistVol, M2=+HAR, M3=+GARCH, M4=+Cascade).
5. **ML comparison** (LightGBM, CatBoost, Elastic Net vs LinearReg) on SPY H2.
6. **Vol-timing CER with transaction costs** (0, 5, 10, 20 bps) on SPY H2 2010-2014 and SPY 2025+.

Run: `python experiments/referee_audit.py`
Output: `results/referee_audit.json`, `results/cer_with_costs.json`, `results/cer_2025.json`

### Audit 2: Consistency-rate simulation

Empirical check on the variance scaling of the cascade slope estimator. The
paper's theory claims Var(beta_hat_t) ~ w^-1 (where w is the cascade window).
This simulation sweeps w and L (z-score lookback) independently on synthetic
AR(1) alpha-mixing data and measures the empirical scaling.

**Headline finding:** the paper's w^-1 claim is NOT supported by simulation.
- log-log slope of Var vs w: +0.20 (variance slightly *grows* in w, does not shrink)
- log-log slope of Var vs L: -0.17 (variance shrinks in L but much slower than L^-1)

This is consistent with the theoretical concern that the four compositions
plus z-score plus OLS-of-4-points structure mean the rate is dominated by
something other than the simple w^-1 or L^-1 of a textbook estimator.

Run: `python experiments/rate_simulation.py`
Output: `results/sim_results.json`

## Files

- `experiments/referee_audit.py` - the 6-audit referee concern script
- `results/referee_audit.json` - referee audit results
- `results/cer_with_costs.json` - H2 2010-2014 vol-timing CER with transaction costs
- `results/cer_2025.json` - 2025+ vol-timing CER with transaction costs
- `experiments/rate_simulation.py` - consistency-rate simulation
- `results/sim_results.json` - simulation results
- `results/REFEREE_AUDIT_README.md` - this file

## How to reproduce

```bash
cd /path/to/volcascade
python experiments/referee_audit.py
python experiments/rate_simulation.py
```

Both scripts are self-contained. They will refresh `data/returns_us.csv` if
missing, otherwise use the existing 2026-07-14 data pull.

## Note on the simulation

The simulation is a Monte Carlo check, not a proof. It empirically answers
"what is the rate of the cascade slope estimator on AR(1) data with rho=0.3?"
The answer (Var ~ O(1) in w, Var ~ O(L^-0.17) in L) is inconsistent with the
w^-1 claim in the paper's theorem. This should be brought to a probability
reviewer before any version of the theorem is published.
