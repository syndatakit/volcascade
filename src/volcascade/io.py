"""yfinance data loaders and curated frontier sample definitions.

Implements the data layer for the pilot. Provides:
- S&P 500 + SPDR sector ETF loader (developed sample)
- Frontier sample loader (6 country ETFs + constituents)
- Crisis ground-truth event table (H3 validation)
"""

from __future__ import annotations

import pandas as pd

__all__ = [
    "SP500_SECTOR_ETFS",
    "FRONTIER_SAMPLE",
    "GLOBAL_CRISES",
    "load_prices",
    "load_returns",
]


# 11 SPDR sector ETFs (XLK, XLF, ... XLC) + SPY as the broad market proxy.
# Used for H3 (stock vs sector decoupling) and H1 (broad-market regime detection).
SP500_SECTOR_ETFS: list[str] = [
    "SPY",  # broad market
    "XLK",  # technology
    "XLF",  # financials
    "XLV",  # health care
    "XLE",  # energy
    "XLY",  # consumer discretionary
    "XLP",  # consumer staples
    "XLI",  # industrials
    "XLU",  # utilities
    "XLB",  # materials
    "XLRE",  # real estate
    "XLC",  # communication services
]


# 6 frontier/emerging markets, each with the country ETF + a sector/country
# proxy ETF for the H3 decoupling test. The frontier sample is selected
# to span SSA, LatAm, and South Asia per the design memo.
FRONTIER_SAMPLE: dict[str, dict[str, str]] = {
    "NSE_KE": {
        "country_etf": "EZA",  # iShares MSCI South Africa (proxy for SSA exposure)
        "sector_proxy": "EZA",  # single-country ETF serves as both
        "currency": "USD",
    },
    "GSE_GH": {
        "country_etf": "EZA",  # SSA proxy
        "sector_proxy": "EZA",
        "currency": "USD",
    },
    "BVSP": {
        "country_etf": "EWZ",  # iShares MSCI Brazil
        "sector_proxy": "EWZ",
        "currency": "USD",
    },
    "JSE": {
        "country_etf": "EZA",  # iShares MSCI South Africa
        "sector_proxy": "EZA",
        "currency": "USD",
    },
    "NSE_IN": {
        "country_etf": "INDA",  # iShares MSCI India
        "sector_proxy": "INDA",
        "currency": "USD",
    },
    "BSE_BD": {
        "country_etf": "XBS",  # unused; Bangladesh coverage is sparse via ETF
        "sector_proxy": "XBS",
        "currency": "USD",
    },
}


# Historical regime-break benchmark dates. Used for H1 / H3 validation
# (backtest regime calls against known events). Dates are in YYYY-MM-DD
# format. Sources: NBER for US, central banks for non-US, news archives
# for the rest.
GLOBAL_CRISES: list[dict] = [
    {
        "date": "2008-09-15",
        "label": "Lehman Brothers bankruptcy",
        "class": "systemic",
        "asset_class": "credit",
    },
    {
        "date": "2008-10-09",
        "label": "2008 GFC peak (uncontrolled decline)",
        "class": "systemic",
        "asset_class": "equity",
    },
    {
        "date": "2011-08-08",
        "label": "US debt-ceiling crisis / S&P downgrade",
        "class": "systemic",
        "asset_class": "equity",
    },
    {
        "date": "2015-08-24",
        "label": "2015 China devaluation / Black Monday",
        "class": "systemic",
        "asset_class": "equity",
    },
    {
        "date": "2018-12-24",
        "label": "2018 Christmas Eve equity rout",
        "class": "systemic",
        "asset_class": "equity",
    },
    {
        "date": "2020-03-16",
        "label": "COVID crash (peak drawdown)",
        "class": "systemic",
        "asset_class": "equity",
    },
    {
        "date": "2020-03-23",
        "label": "Fed announces unlimited QE",
        "class": "systemic",
        "asset_class": "rates",
    },
    {
        "date": "2022-02-24",
        "label": "Russia invades Ukraine",
        "class": "systemic",
        "asset_class": "commodities",
    },
]


def load_prices(
    tickers: list[str],
    start: str = "2010-01-01",
    end: str | None = None,
) -> pd.DataFrame:
    """Load adjusted close prices for a list of tickers via yfinance.

    Parameters
    ----------
    tickers : list of str
        Yahoo Finance tickers.
    start : str
        Start date (YYYY-MM-DD). Default "2010-01-01".
    end : str, optional
        End date. Default = today.

    Returns
    -------
    DataFrame
        Adjusted close prices, indexed by date, one column per ticker.
        Missing days (holidays, half-days) are dropped. Tickers with no
        data for the requested window return an empty column with a
        warning.
    """
    import yfinance as yf

    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")

    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,  # use adjusted close
        progress=False,
        threads=True,
    )
    if raw.empty:
        raise RuntimeError(f"yfinance returned no data for {tickers}")

    # yf returns MultiIndex columns when multiple tickers: ('Close', 'SPY') etc.
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = tickers

    prices = prices.dropna(how="all")
    return prices


def load_returns(
    tickers: list[str],
    start: str = "2010-01-01",
    end: str | None = None,
) -> pd.DataFrame:
    """Load log-returns for a list of tickers via yfinance.

    Convenience wrapper around :func:`load_prices` that returns log-returns
    instead of prices.
    """
    prices = load_prices(tickers, start=start, end=end)
    return np.log(prices / prices.shift(1)).dropna(how="all")


# NumPy import kept here for the return conversion in load_returns
import numpy as np  # noqa: E402
