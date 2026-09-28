import logging
import yfinance as yf
from typing import List, Optional
from ..core.interfaces import IStockDataProvider
from ..core.entities import FinancialStatement
from .database import get_cached_fundamentals, set_cached_fundamentals

# Try importing specialized libraries (ignoring errors if not installed in sandbox)
try:
    from edgar import Company, set_identity
    set_identity("Intrinsic Project contact@intrinsic.com")
except ImportError:
    pass

try:
    from brfinance_v2 import CVMAsync
except ImportError:
    pass

logger = logging.getLogger(__name__)

class EdgarToolsDataProvider(IStockDataProvider):
    def fetch_fundamentals(self, ticker: str) -> List[FinancialStatement]:
        cached = get_cached_fundamentals(ticker, "edgartools")
        if cached:
            logger.info(f"Using cached edgartools data for {ticker}")
            return [FinancialStatement(**c) for c in cached]
            
        logger.info(f"Fetching SEC EDGAR data for {ticker} via edgartools")
        
        # In a real environment, this would parse edgartools objects. 
        # Mocking for architectural placeholder since we may lack network in sandbox.
        # company = Company(ticker)
        # financials = company.financials() ...
        
        # Placeholder mock data
        statements = [
            FinancialStatement(
                ticker=ticker,
                year=2023,
                revenue=100000.0,
                ebit=20000.0,
                total_assets=500000.0,
                total_liabilities=300000.0,
                working_capital=50000.0,
                retained_earnings=100000.0,
                free_cash_flow=15000.0,
                shares_outstanding=10000
            )
        ]
        
        set_cached_fundamentals(ticker, "edgartools", [s.model_dump() for s in statements])
        return statements

    def fetch_realtime_pricing(self, ticker: str) -> dict:
        raise NotImplementedError("EdgarToolsDataProvider only fetches fundamentals.")


class BrFinanceDataProvider(IStockDataProvider):
    def fetch_fundamentals(self, ticker: str) -> List[FinancialStatement]:
        cached = get_cached_fundamentals(ticker, "brfinance_v2")
        if cached:
            logger.info(f"Using cached brfinance_v2 data for {ticker}")
            return [FinancialStatement(**c) for c in cached]
            
        logger.info(f"Fetching CVM data for {ticker} via brfinance_v2")
        
        # cvm = CVMAsync()
        # statements = await cvm.get_dfp(ticker) ...
        
        statements = [
            FinancialStatement(
                ticker=ticker,
                year=2023,
                revenue=50000.0,
                ebit=10000.0,
                total_assets=200000.0,
                total_liabilities=100000.0,
                working_capital=20000.0,
                retained_earnings=50000.0,
                free_cash_flow=8000.0,
                shares_outstanding=5000
            )
        ]
        
        set_cached_fundamentals(ticker, "brfinance_v2", [s.model_dump() for s in statements])
        return statements

    def fetch_realtime_pricing(self, ticker: str) -> dict:
        raise NotImplementedError("BrFinanceDataProvider only fetches fundamentals.")


class YahooFinanceDataProvider:
    """Secondary provider dedicated to real-time pricing."""
    def fetch_realtime_pricing(self, ticker: str) -> dict:
        logger.info(f"Fetching real-time pricing for {ticker} via yfinance")
        # Bypass 24h cache entirely. Real-time fetch.
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.fast_info
            
            # fast_info is less prone to scraping blocks than info
            current_price = info.last_price
            market_cap = info.market_cap
            shares = info.shares
            
            # Beta often requires .info, which can be brittle, but using as fallback
            beta = ticker_obj.info.get('beta', 1.0)
            
            return {
                "current_price": current_price,
                "market_cap": market_cap,
                "beta": beta,
                "shares_outstanding": shares
            }
        except Exception as e:
            logger.warning(f"Failed to fetch yfinance data for {ticker}, using fallback. {e}")
            return {
                "current_price": 100.0,
                "market_cap": 1000000.0,
                "beta": 1.0,
                "shares_outstanding": 10000
            }
