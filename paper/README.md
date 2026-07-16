# Full Paper — Iterated Realized Volatility Cascade

**Compiled PDF (14 pages, 305KB):** https://backend.composio.dev/api/v3/sl/2efmWnM3DI

This is the **full journal-ready paper** for the iterated realized volatility cascade. Use it as a base to trim down if needed.

## Files

- `paper/paper_part1.md` — preamble, abstract, introduction, methodology
- `paper/paper_part2.md` — empirical results (14 subsections)
- `paper/paper_part3.md` — discussion, conclusion, references
- `paper/build_paper.py` — assembles 3 parts into one paper.tex
- `paper/paper.tex` (generated) — single LaTeX file
- `paper/paper.pdf` (generated) — compiled PDF

## Headline results

- Forecast encompassing: Cascade vs HAR $p = 0.0055$
- Clark-West: $p = 0.019$
- DM: Combined vs HAR wins on MSE, MAE, QLIKE
- CER improvement: $+0.138$ over B&H
- Sharpe improvement: $+0.77$
- Max DD improvement: $+0.116$
- 24/24 rolling windows negative
- 99.9\% negative across 720 parameter combinations

## How to compile

```bash
cd paper
python3 build_paper.py
pdflatex paper.tex
```

Already validated: 14-page PDF, no errors.