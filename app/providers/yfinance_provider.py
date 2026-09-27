"""
YFinance data provider strategy implementation.
"""
import logging
from typing import Dict, Any, Optional

import yfinance as yf

from .base import MetricsProvider

logger = logging.getLogger(__name__)


def resolve_price(info: Dict[str, Any], fast_info: Any = None) -> Optional[float]:
    """Resolves current asset price from fast_info or info dictionary."""
    if fast_info and hasattr(fast_info, 'last_price') and fast_info.last_price is not None:
        return fast_info.last_price
    return info.get("currentPrice", info.get("regularMarketPrice"))


def populate_fundamentals(data: Dict[str, Any], info: Dict[str, Any]) -> None:
    """Populates fundamental ratios and margins from yfinance info dictionary.

    yfinance returns ratios/margins as decimals (e.g. 0.15 = 15%),
    so percentage fields are multiplied by 100 to match internal format.
    """
    eps = info.get('trailingEps')
    if eps is not None:
        data['eps'] = round(float(eps), 2)

    pe = info.get('trailingPE')
    if pe is not None:
        data['pe'] = round(float(pe), 2)

    peg = info.get('pegRatio')
    if peg is not None:
        data['peg'] = round(float(peg), 2)

    dy = info.get('dividendYield')
    if dy is not None:
        data['dividend_yield'] = round(float(dy), 2)

    pvpa = info.get('priceToBook')
    if pvpa is not None:
        data['p_vpa'] = round(float(pvpa), 4)

    total_debt = info.get('totalDebt')
    ebitda = info.get('ebitda')
    if total_debt is not None and ebitda and ebitda > 0:
        total_cash = info.get('totalCash', 0) or 0
        net_debt = float(total_debt) - float(total_cash)
        data['debt_ebit'] = round(net_debt / float(ebitda), 2)

    roe = info.get('returnOnEquity')
    if roe is not None:
        data['roe'] = round(float(roe) * 100, 2)

    roa = info.get('returnOnAssets')
    if roa is not None:
        data['roic'] = round(float(roa) * 100, 2)

    margin = info.get('profitMargins')
    if margin is not None:
        data['net_margin'] = round(float(margin) * 100, 2)


def compute_ttm_fcf(ticker: str, data: Dict[str, Any], yf_ticker: yf.Ticker) -> None:
    """Computes trailing twelve months Price / Free Cash Flow (P/FCF)."""
    try:
        info = getattr(yf_ticker, "info", {})
        fast_info = getattr(yf_ticker, "fast_info", None)
        shares = (
            info.get('sharesOutstanding')
            or getattr(fast_info, 'shares', None)
            or info.get('impliedSharesOutstanding')
        )
        price = data.get("price")

        ttm_fcf = None
        quarterly_cashflow = yf_ticker.quarterly_cashflow
        if hasattr(quarterly_cashflow, "index") and 'Free Cash Flow' in quarterly_cashflow.index:
            fcf_quarterly = quarterly_cashflow.loc['Free Cash Flow'].dropna()
            if len(fcf_quarterly) >= 4:
                ttm_fcf = sum(fcf_quarterly.iloc[:4].values)

        if not ttm_fcf:
            annual_cashflow = yf_ticker.cashflow
            if hasattr(annual_cashflow, "index") and 'Free Cash Flow' in annual_cashflow.index:
                fcf_annual = annual_cashflow.loc['Free Cash Flow'].dropna()
                if len(fcf_annual) > 0:
                    ttm_fcf = fcf_annual.iloc[0]

        if price and shares and ttm_fcf:
            fcf_per_share = ttm_fcf / shares
            if fcf_per_share != 0:
                data["p_fcf"] = float(price / fcf_per_share)
    except Exception as e:
        logger.warning("TTM P/FCF calculation failed for %s: %s", ticker, e)


class YFinanceProvider(MetricsProvider):
    """Primary data provider using yfinance."""

    @property
    def name(self) -> str:
        return "yfinance"

    @property
    def priority(self) -> int:
        return 10

    def fetch_stock(self, ticker: str, data: Dict[str, Any], **kwargs) -> None:
        try:
            yf_ticker = yf.Ticker(ticker)
            info = getattr(yf_ticker, "info", {})
            fast_info = getattr(yf_ticker, "fast_info", None)

            price = resolve_price(info, fast_info)
            if price is not None:
                data["price"] = price

            data["name"] = info.get("shortName", ticker)

            market_cap = info.get('marketCap')
            data["market_cap"] = market_cap
            ps_ratio = info.get('priceToSalesTrailing12Months')
            if ps_ratio is not None:
                data["p_s"] = round(float(ps_ratio), 2)

            # P/A and P/NWC calculation
            try:
                bs = yf_ticker.balance_sheet
                if hasattr(bs, 'index') and len(bs.columns) > 0:
                    if 'Total Assets' in bs.index:
                        total_assets = bs.loc['Total Assets'].iloc[0]
                        if market_cap and total_assets and total_assets > 0:
                            data["p_a"] = round(float(market_cap / total_assets), 2)

                    current_assets = bs.loc['Current Assets'].iloc[0] if 'Current Assets' in bs.index else None
                    current_liabilities = bs.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in bs.index else None

                    if current_assets is not None and current_liabilities is not None:
                        nwc = float(current_assets) - float(current_liabilities)
                        if market_cap and nwc > 0:
                            data["p_nwc"] = round(float(market_cap / nwc), 2)
            except Exception as e:
                logger.warning("P/A or P/NWC calculation failed for %s: %s", ticker, e)

            # Core fundamentals
            populate_fundamentals(data, info)

            # P/FCF
            compute_ttm_fcf(ticker, data, yf_ticker)

        except Exception as e:
            logger.error("YFinanceProvider.fetch_stock failed for %s: %s", ticker, e)

    def fetch_reit(self, ticker: str, data: Dict[str, Any], **kwargs) -> None:
        try:
            yf_ticker = yf.Ticker(ticker)
            info = getattr(yf_ticker, "info", {})
            fast_info = getattr(yf_ticker, "fast_info", None)

            price = resolve_price(info, fast_info)
            if price is not None:
                data["price"] = price

            data["name"] = info.get("shortName", ticker)

            dy = info.get("dividendYield")
            if dy is not None:
                data["dividend_yield"] = float(dy)

            ptb = info.get("priceToBook")
            if ptb is not None:
                data["p_vpa"] = round(float(ptb), 4)

            data["min_52w"] = info.get("fiftyTwoWeekLow")
            data["max_52w"] = info.get("fiftyTwoWeekHigh")

            try:
                hist = yf_ticker.history(period="1y")
                if hist is not None and not hist.empty and len(hist) >= 2:
                    first_close = float(hist["Close"].iloc[0])
                    last_close = float(hist["Close"].iloc[-1])
                    if first_close > 0:
                        data["val_12m"] = round(((last_close - first_close) / first_close) * 100, 2)
            except Exception as e:
                logger.debug("Val 12M calculation failed for %s: %s", ticker, e)

            bv = info.get("bookValue")
            if bv is not None:
                data["vp_cota"] = float(bv)

        except Exception as e:
            logger.error("YFinanceProvider.fetch_reit failed for %s: %s", ticker, e)
