"""H3 ground-truth validation: does decoupling order predict event type?

Builds a curated event table (idiosyncratic vs systemic) and tests whether
the cascade decoupling order at the event date predicts the event class.

Idiosyncratic events: AAPL earnings (4/year 2015-2024)
Systemic events: FOMC decisions (8/year), NFP releases (1/month)

For each event, look at the cascade decoupling in a window around the
event and check whether the decoupling order at the event date predicts
whether the event is idiosyncratic or systemic.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from volcascade import build, slope, zscore  # noqa: E402
from volcascade.io import load_prices  # noqa: E402
from volcascade.decoupling import chow_decoupling  # noqa: E402

RESULTS_DIR = ROOT / "results"


def aapl_earnings_dates() -> list[dict]:
    """Curated AAPL earnings dates (calendar dates of release).

    Source: Apple investor relations (publicly known).
    """
    return [
        {"date": "2015-01-27", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY15 earnings"},
        {"date": "2015-04-27", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY15 earnings"},
        {"date": "2015-07-21", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY15 earnings"},
        {"date": "2015-10-27", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY15 earnings"},
        {"date": "2016-01-26", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY16 earnings"},
        {"date": "2016-04-26", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY16 earnings"},
        {"date": "2016-07-26", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY16 earnings"},
        {"date": "2016-10-25", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY16 earnings"},
        {"date": "2017-02-01", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY17 earnings (first after iPhone 7 cycle)"},
        {"date": "2017-05-02", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY17 earnings"},
        {"date": "2017-08-01", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY17 earnings"},
        {"date": "2017-11-02", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY17 earnings (iPhone X)"},
        {"date": "2018-02-01", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY18 earnings"},
        {"date": "2018-05-01", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY18 earnings"},
        {"date": "2018-07-31", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY18 earnings"},
        {"date": "2018-11-01", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY18 earnings"},
        {"date": "2019-01-29", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY19 earnings (China weakness)"},
        {"date": "2019-04-30", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY19 earnings"},
        {"date": "2019-07-30", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY19 earnings"},
        {"date": "2019-10-30", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY19 earnings"},
        {"date": "2020-01-28", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY20 earnings (record)"},
        {"date": "2020-04-30", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY20 earnings (COVID)"},
        {"date": "2020-07-30", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY20 earnings"},
        {"date": "2020-10-29", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY20 earnings"},
        {"date": "2021-01-27", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY21 earnings"},
        {"date": "2021-04-28", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY21 earnings"},
        {"date": "2021-07-27", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY21 earnings"},
        {"date": "2021-10-28", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY21 earnings"},
        {"date": "2022-01-27", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY22 earnings"},
        {"date": "2022-04-28", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY22 earnings"},
        {"date": "2022-07-28", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY22 earnings"},
        {"date": "2022-10-27", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY22 earnings"},
        {"date": "2023-02-02", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY23 earnings"},
        {"date": "2023-05-04", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY23 earnings"},
        {"date": "2023-08-03", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY23 earnings"},
        {"date": "2023-11-02", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY23 earnings"},
        {"date": "2024-02-01", "asset": "AAPL", "class": "idiosyncratic", "label": "Q1 FY24 earnings"},
        {"date": "2024-05-02", "asset": "AAPL", "class": "idiosyncratic", "label": "Q2 FY24 earnings"},
        {"date": "2024-08-01", "asset": "AAPL", "class": "idiosyncratic", "label": "Q3 FY24 earnings"},
        {"date": "2024-10-31", "asset": "AAPL", "class": "idiosyncratic", "label": "Q4 FY24 earnings"},
    ]


def fomc_dates() -> list[dict]:
    """Curated FOMC decision dates (announcement days, 2015-2024)."""
    dates = [
        # 2015
        "2015-01-28", "2015-03-18", "2015-04-29", "2015-06-17", "2015-07-29",
        "2015-09-17", "2015-10-28", "2015-12-16",
        # 2016
        "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27",
        "2016-09-21", "2016-11-02", "2016-12-14",
        # 2017
        "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26",
        "2017-09-20", "2017-11-01", "2017-12-13",
        # 2018
        "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01",
        "2018-09-26", "2018-11-08", "2018-12-19",
        # 2019
        "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31",
        "2019-09-18", "2019-10-30", "2019-12-11",
        # 2020
        "2020-01-29", "2020-03-03", "2020-03-15", "2020-04-29", "2020-06-10",
        "2020-07-29", "2020-09-16", "2020-11-05", "2020-12-16",
        # 2021
        "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28",
        "2021-09-22", "2021-11-03", "2021-12-15",
        # 2022
        "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27",
        "2022-09-21", "2022-11-02", "2022-12-14",
        # 2023
        "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26",
        "2023-09-20", "2023-11-01", "2023-12-13",
        # 2024
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31",
        "2024-09-18", "2024-11-07", "2024-12-18",
    ]
    return [{"date": d, "asset": "FOMC", "class": "systemic", "label": "FOMC decision"} for d in dates]


def main() -> None:
    print("=" * 78)
    print("H3 ground-truth: decoupling order predicts event type")
    print("=" * 78)

    # Curated event table
    events = aapl_earnings_dates() + fomc_dates()
    print(f"\n{len(events)} curated events:")
    print(f"  idiosyncratic (AAPL earnings): {sum(1 for e in events if e['class']=='idiosyncratic')}")
    print(f"  systemic (FOMC): {sum(1 for e in events if e['class']=='systemic')}")

    # Load AAPL + XLK + SPY
    print("\nloading AAPL, XLK, SPY (2015-2024)...")
    t0 = time.time()
    prices = load_prices(["AAPL", "XLK", "SPY"], start="2015-01-01", end="2024-12-31")
    returns = np.log(prices / prices.shift(1)).dropna()
    print(f"  loaded {returns.shape[0]} days in {time.time()-t0:.1f}s\n")

    # For AAPL events: decoupling between AAPL and its sector (XLK)
    # For FOMC events: decoupling between SPY and SPY (should be none) — or use
    # a more meaningful test: decoupling between AAPL and sector
    print("computing cascade + decoupling at each event date...")

    # Build cascades
    aapl_cascade = build(returns["AAPL"], orders=(1, 2, 3, 4), inner_window=10)
    aapl_z = zscore(aapl_cascade, lookback=120)
    xlk_cascade = build(returns["XLK"], orders=(1, 2, 3, 4), inner_window=10)
    xlk_z = zscore(xlk_cascade, lookback=120)
    spy_cascade = build(returns["SPY"], orders=(1, 2, 3, 4), inner_window=10)
    spy_z = zscore(spy_cascade, lookback=120)

    # For each event, compute decoupling order at the event date
    records = []
    t0 = time.time()
    for i, ev in enumerate(events):
        if (i + 1) % 20 == 0:
            print(f"  event {i+1}/{len(events)}  ({time.time()-t0:.1f}s)")
        d = pd.Timestamp(ev["date"])
        if d not in returns.index:
            continue  # skip non-trading days

        # Get decoupling between AAPL and XLK at this event
        # Look at the 60-day window ending at the event date
        end_loc = returns.index.get_loc(d)
        start_loc = max(0, end_loc - 60)
        if end_loc - start_loc < 30:
            continue
        aapl_window = aapl_z[1].iloc[start_loc:end_loc + 1].dropna()
        xlk_window = xlk_z[1].iloc[start_loc:end_loc + 1].dropna()
        common = aapl_window.index.intersection(xlk_window.index)
        if len(common) < 30:
            continue
        aapl_s = aapl_window.loc[common]
        xlk_s = xlk_window.loc[common]
        out = chow_decoupling(aapl_s, xlk_s, max_order=1, lookback=15, alpha=0.05)
        max_f, min_p = out["f_statistics"][1]
        decoupling_detected = (min_p < 0.05)
        records.append({
            "date": ev["date"],
            "label": ev["label"],
            "class": ev["class"],
            "asset": ev["asset"],
            "max_F": float(max_f),
            "min_p": float(min_p),
            "decoupling_detected": bool(decoupling_detected),
        })

    df = pd.DataFrame(records)
    print(f"\nanalyzed {len(df)} events (some skipped if not on trading day)")

    # Compare decoupling detection by event class
    print("\n" + "=" * 78)
    print("RESULTS: decoupling detection by event class")
    print("=" * 78)
    for cls in ["idiosyncratic", "systemic"]:
        sub = df[df["class"] == cls]
        if len(sub) == 0:
            continue
        detect_rate = sub["decoupling_detected"].mean()
        print(f"\n  {cls} (n={len(sub)}):")
        print(f"    decoupling detected: {int(sub['decoupling_detected'].sum())}/{len(sub)} ({detect_rate:.1%})")
        print(f"    mean max_F: {sub['max_F'].mean():.2f}")
        print(f"    mean min_p: {sub['min_p'].mean():.4f}")

    # Test: are AAPL earnings more likely to show decoupling than FOMC?
    idio = df[df["class"] == "idiosyncratic"]["decoupling_detected"].astype(int)
    sys_ = df[df["class"] == "systemic"]["decoupling_detected"].astype(int)
    if len(idio) > 5 and len(sys_) > 5:
        # Fisher exact test
        from scipy.stats import fisher_exact
        table = [[int(idio.sum()), int(len(idio) - idio.sum())],
                 [int(sys_.sum()), int(len(sys_) - sys_.sum())]]
        odds, p_fisher = fisher_exact(table)
        print(f"\n  Fisher exact: odds_ratio = {odds:.3f}, p = {p_fisher:.4f}")
        if p_fisher < 0.05:
            print(f"  --> AAPL earnings are {'MORE' if idio.mean() > sys_.mean() else 'LESS'} likely to show decoupling than FOMC (p<0.05)")

    # Mann-Whitney on max_F
    if len(idio) > 5 and len(sys_) > 5:
        u, p_mw = sps.mannwhitneyu(
            df[df["class"] == "idiosyncratic"]["max_F"],
            df[df["class"] == "systemic"]["max_F"],
            alternative="two-sided",
        )
        print(f"  Mann-Whitney on max_F: U={u:.0f}, p={p_mw:.4f}")

    # Save results
    out_path = RESULTS_DIR / "h3_ground_truth.json"
    with open(out_path, "w") as f:
        json.dump({
            "events": [r for r in records],
            "summary": {
                "n_total": int(len(df)),
                "n_idiosyncratic": int(len(df[df["class"] == "idiosyncratic"])),
                "n_systemic": int(len(df[df["class"] == "systemic"])),
                "idio_decoupling_rate": float(df[df["class"] == "idiosyncratic"]["decoupling_detected"].mean()),
                "sys_decoupling_rate": float(df[df["class"] == "systemic"]["decoupling_detected"].mean()),
            },
        }, f, indent=2)
    print(f"\nresults saved to {out_path}")


if __name__ == "__main__":
    main()
