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
        "dividend_yield": None, "p_vpa": None,
        "min_52w": None, "max_52w": None, "val_12m": None, "vp_cota": None,
        "caixa": None, "dy_cagr": None, "val_cagr": None, "cotistas": None
    }

def _get_statusinvest_data(ticker: str, data: Dict[str, Any], is_br: bool = True, is_us_reit: bool = False) -> None:
    si_ticker = ticker.replace(".SA", "").replace(".sa", "").upper()
    try:
        url_path = 'acao' if is_br else ('reit' if is_us_reit else 'stock')
        url = f'https://statusinvest.com.br/{url_path}/indicatorhistoricallist'
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

def fetch_stock_metrics(ticker: str, is_us_reit: bool = False) -> Dict[str, Any]:
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

        is_br = ticker.endswith(".SA")
        if is_br:
            _get_statusinvest_data(ticker, data, is_br=True)
        else:
            _get_statusinvest_data(ticker, data, is_br=False, is_us_reit=is_us_reit)
            
            # ANOMALY ESCUDO: Filter out hyperinflation Status Invest glitches for ADRs (like ARS)
            try:
                info = getattr(tc, "info", {})
                if data.get("roe") is not None and abs(data["roe"]) > 1000:
                    yf_roe = info.get("returnOnEquity")
                    data["roe"] = yf_roe * 100 if yf_roe is not None else None
                
                if data.get("roic") is not None and abs(data["roic"]) > 1000:
                    yf_roa = info.get("returnOnAssets")
                    # Fallback to ROA since Yahoo Finance doesn't explicitly expose strict ROIC publicly in the .info dictionary
                    data["roic"] = yf_roa * 100 if yf_roa is not None else None
            except Exception as bug:
                print(f"Failed to apply anomaly filter for {ticker}: {bug}")
            
        _compute_ttm_fcf(ticker, data, tc)
    except Exception as e:
        print(f"yfinance price error for {ticker}: {e}")
        
    return data

def fetch_reit_metrics(ticker: str) -> Dict[str, Any]:
    """Fetches FII/REIT metrics target."""
    data = _init_empty_metrics(ticker)
    from bs4 import BeautifulSoup
    def str_to_float(s):
        if not s or s == '-': return None
        s = s.replace('%', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
        try: return float(s)
        except: return None
        
    try:
        si_ticker = ticker.replace(".SA", "").upper()
        url = f'https://statusinvest.com.br/fundos-imobiliarios/{si_ticker.lower()}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = status_invest_session.get(url, headers=headers)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            name_tag = soup.find('h1')
            if name_tag:
                data["name"] = name_tag.text.split('-')[-1].strip()
            
            for title in soup.find_all('h3', class_='title'):
                val_tag = title.find_next('strong', class_='value')
                if val_tag:
                    txt = title.text.strip().lower()
                    val = str_to_float(val_tag.text.strip())
                    if 'valor atual' in txt: data['price'] = val
                    elif 'min. 52 semanas' in txt: data['min_52w'] = val
                    elif 'máx. 52 semanas' in txt: data['max_52w'] = val
                    elif 'dividend yield' in txt: data['dividend_yield'] = val
                    elif 'valorização (12m)' in txt: data['val_12m'] = val
                    elif 'val. patrimonial p/cota' in txt: data['vp_cota'] = val
                    elif 'p/vp' in txt: data['p_vpa'] = val
                    elif 'valor em caixa' in txt: data['caixa'] = val
                    elif 'dy cagr (3 anos)' in txt: data['dy_cagr'] = val
                    elif 'valor cagr (3 anos)' in txt: data['val_cagr'] = val
                    elif 'cotistas' in txt: data['cotistas'] = int(val) if val else None
    except Exception as e:
        print(f"Error fetching REIT {ticker}: {e}")
    return data
