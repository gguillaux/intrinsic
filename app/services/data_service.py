import yfinance as yf
import requests_cache
from datetime import timedelta
from typing import Dict, Any

# Create a cached session specifically for yfinance if global isn't picked up
session = requests_cache.CachedSession('intrinsic_yfinance.cache', expire_after=timedelta(hours=6))

import requests

def fetch_stock_metrics(ticker: str) -> Dict[str, Any]:
    """
    Fetches stock metrics. Combines yfinance for price and Status Invest for fundamentals.
    """
    # Fix ticker for StatusInvest (remove .SA)
    si_ticker = ticker.replace(".SA", "").replace(".sa", "").upper()
    
    # Init default data with None
    data = {
        "ticker": ticker,
        "name": ticker,
        "price": None,
        "fcf": None, 
        "eps": None,
        "debt": None, 
        "pe": None, 
        "peg": None, 
        "dividend_yield": None, 
        "p_vpa": None
    }
    
    try:
        # 1. Get Price from yfinance without cache session
        t = yf.Ticker(ticker)
        info = t.fast_info if hasattr(t, "fast_info") else t.info
        data["price"] = getattr(info, "last_price", info.get("currentPrice", info.get("regularMarketPrice")))
        if hasattr(t, "info"):
            data["name"] = t.info.get("shortName", ticker)
    except Exception as e:
        print(f"yfinance price error for {ticker}: {e}")

    # 2. Get Indicators from Status Invest API if BR stock
    if ticker.endswith(".SA"):
        try:
            url = 'https://statusinvest.com.br/acao/indicatorhistoricallist'
            params = {
                'codes': si_ticker,
                'time': 5,
                'byQuarter': 'false',
                'futureData': 'false'
            }
            headers = {'Accept': '*/*', 'User-Agent': 'insomnia/9.2.0'}
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                json_comp = response.json()
                if 'data' in json_comp and json_comp['data']:
                    first_key = list(json_comp['data'].keys())[0]
                    indicators = json_comp['data'][first_key]
                    
                    for item in indicators:
                        k = item.get('key')
                        v = item.get('actual')
                        if k == 'lpa': data['eps'] = v
                        elif k == 'p_l': data['pe'] = v
                        elif k == 'peg_Ratio': data['peg'] = v
                        elif k == 'dy': data['dividend_yield'] = v
                        elif k == 'p_vp': data['p_vpa'] = v
                        elif k == 'dividaliquida_patrimonioliquido': data['debt'] = v
        except Exception as e:
            print(f"StatusInvest error for {ticker}: {e}")
    else:
        # US Stocks logic (keep yfinance)
        try:
            if hasattr(t, "info"):
                data["eps"] = t.info.get("trailingEps")
                data["pe"] = t.info.get("trailingPE")
                data["peg"] = t.info.get("pegRatio")
                data["dividend_yield"] = t.info.get("dividendYield", 0) * 100 if t.info.get("dividendYield") else None
                data["p_vpa"] = t.info.get("priceToBook")
                data["fcf"] = t.info.get("freeCashflow")
                data["debt"] = t.info.get("totalDebt")
        except:
            pass
            
    return data

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
