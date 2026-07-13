# volcascade

**The Volatility Cascade: A Term Structure of Differentiation Order for Detecting Regime Breaks and Idiosyncratic Risk, Across Developed and Frontier Markets.**

A Python package and companion paper that constructs a multi-order iterated-realized-volatility statistic (the *volatility cascade*) and uses it to classify regime entry, mark regime exit, decouple idiosyncratic from systemic risk, and test whether these dynamics hold in frontier markets.

## What is the volatility cascade?

Volatility-of-volatility is well established at a single order (vol-of-vol, VVIX, options-implied measures), but the literature stops there. The **volatility cascade** treats the full ladder of iterated volatility-of-volatility (order 1 through N) as a joint object — analogous to how the VIX term structure across maturities is more informative than any single VIX level. The informative axis is **differentiation order**, not time.

```
returns          → order-1 vol (realized volatility)
order-1 vol      → order-2 vol (vol-of-vol)
order-2 vol      → order-3 vol (vol-of-vol-of-vol)
order-3 vol      → order-4 vol
```

The shape of the cascade (flat vs. steepening vs. inverted) at each time `t` is summarized as a one-number **cascade slope** — the regression slope of order index against z-scored volatilities.

## Hypotheses

- **H1 (regime entry):** cascade shape classifies genuine regime breaks better than any single order alone.
- **H2 (regime exit):** cascade convergence (higher orders decaying faster than order-1) marks regime exit earlier or more reliably than order-1 alone crossing its moving average.
- **H3 (decoupling):** cross-sectional cascade divergence between a stock and its sector/index — the order at which their cascades decouple — distinguishes idiosyncratic from systemic volatility events, *without options data*.
- **H4 (cross-market):** cascade informativeness differs systematically between developed markets and frontier/emerging markets with thinner liquidity and slower price discovery.

## Repo layout

- `docs/DESIGN_MEMO.md` — locked methodology + package design (1 page)
- `src/volcascade/` — package source (cascade, decoupling, baselines, regime, io, viz)
- `tests/` — pytest test suite
- `experiments/` — pilot scripts and notebooks
- `paper/` — manuscript source (LaTeX/Markdown)

## Status

Active development. See `docs/DESIGN_MEMO.md` for the locked design decisions and the deliverable sequence.

## Authors

- **Nitya Hapani** — lead author, research design, paper writing, application narrative
- **pong** — implementation, methodology, code, pilot experiments, package release

## License

MIT — see `LICENSE`.
