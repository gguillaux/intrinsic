import yfinance as yf
from typing import Dict, Any

def fetch_stock_metrics(ticker: str) -> Dict[str, Any]:
    """
    Fetches stock metrics from yfinance for a given ticker.
    Target metrics for Stocks: FCF, EPS, Debt, P/E, PEG
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # Calculate trailing FCF from cashflow if freeCashflow metric is missing, else use info
        fcf = info.get("freeCashflow")
        
        # In yfinance, P/E is often trailingPE, EPS is trailingEps
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
        t = yf.Ticker(ticker)
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
