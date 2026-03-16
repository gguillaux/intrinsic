import yfinance as yf
import requests_cache
from datetime import timedelta
from typing import Dict, Any

# Create a cached session specifically for yfinance if global isn't picked up
session = requests_cache.CachedSession('intrinsic_yfinance.cache', expire_after=timedelta(hours=6))

def fetch_stock_metrics(ticker: str) -> Dict[str, Any]:
    """
    Fetches stock metrics from yfinance for a given ticker, cached.
    """
    try:
        t = yf.Ticker(ticker, session=session)
        info = t.info
        
        fcf = info.get("freeCashflow")
        
        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "price": info.get("currentPrice", info.get("regularMarketPrice")),
            "fcf": fcf,
            "eps": info.get("trailingEps"),
            "debt": info.get("totalDebt"),
            "pe": info.get("trailingPE"),
            "peg": info.get("pegRatio"),
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
            "p_vpa": info.get("priceToBook")
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return {
            "ticker": ticker,
            "name": None, "price": None, "fcf": None, "eps": None,
            "debt": None, "pe": None, "peg": None, "dividend_yield": None, "p_vpa": None
        }

def fetch_reit_metrics(ticker: str) -> Dict[str, Any]:
    """
    Fetches FII/REIT metrics. Target: DivYield, P/VPA.
    """
    try:
        t = yf.Ticker(ticker, session=session)
        info = t.info
        
        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "price": info.get("currentPrice", info.get("regularMarketPrice")),
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
            "p_vpa": info.get("priceToBook"),
            "fcf": None, "eps": None, "debt": None, "pe": None, "peg": None
        }
    except Exception as e:
        print(f"Error fetching REIT {ticker}: {e}")
        return {
            "ticker": ticker,
            "name": None, "price": None, "fcf": None, "eps": None,
            "debt": None, "pe": None, "peg": None, "dividend_yield": None, "p_vpa": None
        }
