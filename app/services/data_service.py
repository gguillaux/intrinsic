import yfinance as yf
import requests_cache
from datetime import timedelta
from typing import Dict, Any

# Create a cached session for status invest (24h)
status_invest_session = requests_cache.CachedSession('intrinsic_statusinvest.cache', expire_after=timedelta(hours=24))

def _init_empty_metrics(ticker: str) -> Dict[str, Any]:
    return {
        "ticker": ticker, "name": ticker, "price": None,
        "p_fcf": None, "pe": None, "eps": None, "debt_ebit": None,
        "roic": None, "roe": None, "net_margin": None, "peg": None, 
        "dividend_yield": None, "p_vpa": None
    }

def _get_statusinvest_data(ticker: str, data: Dict[str, Any]) -> None:
    si_ticker = ticker.replace(".SA", "").replace(".sa", "").upper()
    try:
        url = 'https://statusinvest.com.br/acao/indicatorhistoricallist'
        payload = {'codes[]': si_ticker, 'time': '7', 'byQuarter': 'false', 'futureData': 'false'}
        headers = {
            'Accept': '*/*', 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        res = status_invest_session.post(url, data=payload, headers=headers)
        if res.status_code == 200:
            json_comp = res.json()
            if 'data' in json_comp and json_comp['data']:
                first_key = list(json_comp['data'].keys())[0]
                for item in json_comp['data'][first_key]:
                    k, v = item.get('key'), item.get('actual')
                    mapping = {
                        'lpa': 'eps', 'p_l': 'pe', 'peg_Ratio': 'peg', 'dy': 'dividend_yield',
                        'p_vp': 'p_vpa', 'dividaliquida_ebit': 'debt_ebit', 
                        'roic': 'roic', 'roe': 'roe', 'margemliquida': 'net_margin'
                    }
                    if k in mapping: data[mapping[k]] = v
    except Exception as e:
        print(f"StatusInvest error for {ticker}: {e}")

def _get_yfinance_fundamentals(ticker: str, data: Dict[str, Any], tc: yf.Ticker) -> None:
    try:
        info = getattr(tc, "info", {})
        data["eps"] = info.get("trailingEps")
        data["pe"] = info.get("trailingPE")
        data["peg"] = info.get("pegRatio")
        data["dividend_yield"] = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None
        data["p_vpa"] = info.get("priceToBook")
        data["roe"] = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None
        data["net_margin"] = info.get("profitMargins", 0) * 100 if info.get("profitMargins") else None
    except Exception as e:
        print(f"yfinance fundamentals error for {ticker}: {e}")

def _compute_ttm_fcf(ticker: str, data: Dict[str, Any], tc: yf.Ticker) -> None:
    try:
        info = getattr(tc, "info", {})
        fast_info = getattr(tc, "fast_info", None)
        shares = info.get('sharesOutstanding') or getattr(fast_info, 'shares', None) or info.get('impliedSharesOutstanding')
        price = data.get("price")
        
        ttm_fcf = None
        qcf = tc.quarterly_cashflow
        if hasattr(qcf, "index") and 'Free Cash Flow' in qcf.index:
            fcf_q = qcf.loc['Free Cash Flow'].dropna()
            if len(fcf_q) >= 4:
                ttm_fcf = sum(fcf_q.iloc[:4].values)
                
        if not ttm_fcf:
            acf = tc.cashflow
            if hasattr(acf, "index") and 'Free Cash Flow' in acf.index:
                fcf_a = acf.loc['Free Cash Flow'].dropna()
                if len(fcf_a) > 0:
                    ttm_fcf = fcf_a.iloc[0]

        if price and shares and ttm_fcf:
            fcf_per_share = ttm_fcf / shares
            if fcf_per_share != 0:
                data["p_fcf"] = float(price / fcf_per_share)
    except Exception as e:
        print(f"Manual TTM P/FCF error for {ticker}: {e}")

def fetch_stock_metrics(ticker: str) -> Dict[str, Any]:
    """Fetches stock metrics into a unified dictionary format."""
    data = _init_empty_metrics(ticker)
    try:
        tc = yf.Ticker(ticker)
        # Parse Price and Name uniformly
        info = getattr(tc, "info", {})
        fast_info = getattr(tc, "fast_info", None)
        
        # Determine exact price
        if fast_info and hasattr(fast_info, 'last_price'):
            data["price"] = fast_info.last_price
        else:
            data["price"] = info.get("currentPrice", info.get("regularMarketPrice"))
            
        data["name"] = info.get("shortName", ticker)

        if ticker.endswith(".SA"):
            _get_statusinvest_data(ticker, data)
        else:
            _get_yfinance_fundamentals(ticker, data, tc)
            
        _compute_ttm_fcf(ticker, data, tc)
    except Exception as e:
        print(f"yfinance price error for {ticker}: {e}")
        
    return data

def fetch_reit_metrics(ticker: str) -> Dict[str, Any]:
    """Fetches FII/REIT metrics target."""
    data = _init_empty_metrics(ticker)
    try:
        t = yf.Ticker(ticker)
        info = getattr(t, "info", {})
        data["name"] = info.get("shortName", ticker)
        data["price"] = info.get("currentPrice", info.get("regularMarketPrice"))
        dy = info.get("dividendYield")
        data["dividend_yield"] = dy * 100 if dy else None
        data["p_vpa"] = info.get("priceToBook")
    except Exception as e:
        print(f"Error fetching REIT {ticker}: {e}")
    return data
