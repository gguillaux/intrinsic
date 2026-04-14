import yfinance as yf
import requests_cache
from datetime import timedelta
from typing import Dict, Any

# Create a cached session specifically for yfinance if global isn't picked up
session = requests_cache.CachedSession('intrinsic_yfinance.cache', expire_after=timedelta(hours=6))

# Create a cached session for status invest (24h)
status_invest_session = requests_cache.CachedSession('intrinsic_statusinvest.cache', expire_after=timedelta(hours=24))

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
        "p_fcf": None, 
        "pe": None, 
        "eps": None,
        "debt_ebit": None, 
        "roic": None,
        "roe": None,
        "net_margin": None,
        "peg": None, 
        "dividend_yield": None, 
        "p_vpa": None
    }
    
    # 1. Check if BR stock
    if ticker.endswith(".SA"):
        try:
            t = yf.Ticker(ticker, session=session)
            info = t.fast_info if hasattr(t, "fast_info") else t.info
            data["price"] = getattr(info, "last_price", info.get("currentPrice", info.get("regularMarketPrice")))
            if hasattr(t, "info"):
                data["name"] = t.info.get("shortName", ticker)
        except Exception as e:
            print(f"yfinance price error for {ticker}: {e}")

        try:
            url = 'https://statusinvest.com.br/acao/indicatorhistoricallist'
            payload = {
                'codes[]': si_ticker,
                'time': '7',
                'byQuarter': 'false',
                'futureData': 'false'
            }
            headers = {
                'Accept': '*/*', 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = status_invest_session.post(url, data=payload, headers=headers)
            
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
                        elif k == 'dividaliquida_ebit': data['debt_ebit'] = v
                        elif k == 'roic': data['roic'] = v
                        elif k == 'roe': data['roe'] = v
                        elif k == 'margemliquida': data['net_margin'] = v
        except Exception as e:
            print(f"StatusInvest error for {ticker}: {e}")
            
    else:
        # US Stocks logic (keep yfinance completely for them)
        try:
            t = yf.Ticker(ticker, session=session)
            info = t.fast_info if hasattr(t, "fast_info") else t.info
            data["price"] = getattr(info, "last_price", info.get("currentPrice", info.get("regularMarketPrice")))
            if hasattr(t, "info"):
                data["name"] = t.info.get("shortName", ticker)
                
            if hasattr(t, "info"):
                data["eps"] = t.info.get("trailingEps")
                data["pe"] = t.info.get("trailingPE")
                data["peg"] = t.info.get("pegRatio")
                data["dividend_yield"] = t.info.get("dividendYield", 0) * 100 if t.info.get("dividendYield") else None
                data["p_vpa"] = t.info.get("priceToBook")
                data["debt_ebit"] = None
                data["roic"] = None
                data["roe"] = t.info.get("returnOnEquity", 0) * 100 if t.info.get("returnOnEquity") else None
                data["net_margin"] = t.info.get("profitMargins", 0) * 100 if t.info.get("profitMargins") else None
        except Exception as e:
            print(f"yfinance fundamentals error for {ticker}: {e}")
            
    # Universal Robust TTM P/FCF Calculation
    try:
        tc = yf.Ticker(ticker, session=session)
        # 1. Price
        current_price = data.get("price") or getattr(tc.fast_info, 'last_price', None) or tc.info.get("currentPrice") or tc.info.get("previousClose")
        
        # 2. Shares Outstanding
        shares = tc.info.get('sharesOutstanding') or getattr(tc.fast_info, 'shares', None) or tc.info.get('impliedSharesOutstanding')
        
        # 3. FCF (Trailing Twelve Months from Quarterly)
        ttm_fcf = None
        qcf = tc.quarterly_cashflow
        if hasattr(qcf, "index") and 'Free Cash Flow' in qcf.index:
            fcf_q = qcf.loc['Free Cash Flow'].dropna()
            if len(fcf_q) >= 4:
                ttm_fcf = sum(fcf_q.iloc[:4].values)
                
        # 4. Fallback to Annual FCF if TTM Quarterly is missing
        if not ttm_fcf:
            acf = tc.cashflow
            if hasattr(acf, "index") and 'Free Cash Flow' in acf.index:
                fcf_a = acf.loc['Free Cash Flow'].dropna()
                if len(fcf_a) > 0:
                    ttm_fcf = fcf_a.iloc[0]

        # 5. Calculation
        if current_price and shares and ttm_fcf:
            fcf_per_share = ttm_fcf / shares
            if fcf_per_share != 0:
                data["p_fcf"] = float(current_price / fcf_per_share)
    except Exception as e:
        print(f"Manual TTM P/FCF error for {ticker}: {e}")

    return data

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
            "p_fcf": None, "pe": None, "eps": None, "debt_ebit": None, "peg": None,
            "roic": None, "roe": None, "net_margin": None
        }
    except Exception as e:
        print(f"Error fetching REIT {ticker}: {e}")
        return {
            "ticker": ticker,
            "name": None, "price": None, "p_fcf": None, "pe": None, "eps": None,
            "debt_ebit": None, "peg": None, "dividend_yield": None, "p_vpa": None,
            "roic": None, "roe": None, "net_margin": None
        }
