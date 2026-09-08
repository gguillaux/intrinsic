import logging
import threading
import json
import datetime
from datetime import timedelta
from typing import Dict, Any

import yfinance as yf
import requests_cache
from bs4 import BeautifulSoup

from ..models import ParsedMetricsCache
from ..config import (
    REQUEST_TIMEOUT,
    ANOMALY_THRESHOLD,
    STATUS_INVEST_HEADERS,
    STATUSINVEST_INDICATOR_MAPPING,
    DEFAULT_CACHE_HOURS,
    FII_CATEGORIES,
)

logger = logging.getLogger(__name__)

# --- Thread-safe cached session (R2) ---
_session_lock = threading.Lock()
_status_invest_session: requests_cache.CachedSession | None = None
_cache_hours: int = DEFAULT_CACHE_HOURS


def _get_session() -> requests_cache.CachedSession:
    """Returns the thread-safe cached session singleton."""
    global _status_invest_session
    with _session_lock:
        if _status_invest_session is None:
            _status_invest_session = requests_cache.CachedSession(
                'intrinsic_statusinvest.cache',
                expire_after=timedelta(hours=_cache_hours)
            )
        return _status_invest_session


def update_cache_expiration(hours: int):
    """Updates the HTTP cache session expiration. Thread-safe."""
    global _status_invest_session, _cache_hours
    with _session_lock:
        _cache_hours = hours
        _status_invest_session = requests_cache.CachedSession(
            'intrinsic_statusinvest.cache',
            expire_after=timedelta(hours=hours)
        )


def _get_cache_hours() -> int:
    return _cache_hours


def _is_valid_data(data: Dict[str, Any]) -> bool:
    return data.get("price") is not None


def _init_empty_metrics(ticker: str) -> Dict[str, Any]:
    return {
        "ticker": ticker, "name": ticker, "price": None,
        "market_cap": None, "p_s": None,
        "p_fcf": None, "pe": None, "p_a": None, "p_nwc": None,
        "eps": None, "debt_ebit": None,
        "roic": None, "roe": None, "net_margin": None, "peg": None,
        "dividend_yield": None, "p_vpa": None,
        "min_52w": None, "max_52w": None, "val_12m": None, "vp_cota": None,
        "caixa": None, "dy_cagr": None, "val_cagr": None, "cotistas": None
    }


def _populate_yfinance_fundamentals(data: Dict[str, Any], info: Dict[str, Any]) -> None:
    """Populates fundamental metrics from yfinance info as primary data source.

    This makes the app independent of StatusInvest for core metrics.
    yfinance returns ratios/margins as decimals (e.g. 0.15 = 15%),
    so percentage fields are multiplied by 100 to match the internal format.
    """
    # EPS (Earnings Per Share) — currency units, no conversion needed
    eps = info.get('trailingEps')
    if eps is not None:
        data['eps'] = round(float(eps), 2)

    # P/E (Price-to-Earnings) — ratio, no conversion needed
    pe = info.get('trailingPE')
    if pe is not None:
        data['pe'] = round(float(pe), 2)

    # PEG Ratio — ratio, no conversion needed
    peg = info.get('pegRatio')
    if peg is not None:
        data['peg'] = round(float(peg), 2)

    # Dividend Yield — yfinance returns as percentage (0.34 = 0.34%)
    dy = info.get('dividendYield')
    if dy is not None:
        data['dividend_yield'] = round(float(dy), 2)

    # P/VPA (Price to Book) — ratio, no conversion needed
    pvpa = info.get('priceToBook')
    if pvpa is not None:
        data['p_vpa'] = round(float(pvpa), 4)

    # Debt/EBIT — approximate as Net Debt / EBITDA
    total_debt = info.get('totalDebt')
    ebitda = info.get('ebitda')
    if total_debt is not None and ebitda and ebitda > 0:
        total_cash = info.get('totalCash', 0) or 0
        net_debt = float(total_debt) - float(total_cash)
        data['debt_ebit'] = round(net_debt / float(ebitda), 2)

    # ROE — yfinance returns decimal (0.15 = 15%), convert to %
    roe = info.get('returnOnEquity')
    if roe is not None:
        data['roe'] = round(float(roe) * 100, 2)

    # ROIC — yfinance has no direct ROIC; approximate with ROA
    roa = info.get('returnOnAssets')
    if roa is not None:
        data['roic'] = round(float(roa) * 100, 2)

    # Net Margin — yfinance returns decimal (0.25 = 25%), convert to %
    margin = info.get('profitMargins')
    if margin is not None:
        data['net_margin'] = round(float(margin) * 100, 2)


def _parse_brazilian_currency(text: str):
    """Parses Brazilian-formatted numbers (e.g. 'R$ 1.234,56' or '12,34%') to float."""
    if not text or text == '-':
        return None
    text = text.replace('%', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


# --- External API Fetchers ---

def _get_statusinvest_data(ticker: str, data: Dict[str, Any], is_br: bool = True, is_us_reit: bool = False) -> None:
    statusinvest_ticker = ticker.replace(".SA", "").replace(".sa", "").upper()
    try:
        url_path = 'acao' if is_br else ('reit' if is_us_reit else 'stock')
        url = f'https://statusinvest.com.br/{url_path}/indicatorhistoricallist'
        payload = {'codes[]': statusinvest_ticker, 'time': '7', 'byQuarter': 'false', 'futureData': 'false'}

        response = _get_session().post(url, data=payload, headers=STATUS_INVEST_HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            json_body = response.json()
            if 'data' in json_body and json_body['data']:
                first_key = list(json_body['data'].keys())[0]
                for item in json_body['data'][first_key]:
                    indicator_key = item.get('key')
                    indicator_value = item.get('actual')
                    if indicator_key in STATUSINVEST_INDICATOR_MAPPING:
                        if indicator_value is not None:
                            data[STATUSINVEST_INDICATOR_MAPPING[indicator_key]] = indicator_value
    except Exception as e:
        logger.warning("StatusInvest fetch failed for %s: %s", ticker, e)


def _compute_ttm_fcf(ticker: str, data: Dict[str, Any], yf_ticker: yf.Ticker) -> None:
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


def _apply_anomaly_filter(ticker: str, data: Dict[str, Any], yf_ticker: yf.Ticker) -> None:
    """Filters out hyperinflated metrics from StatusInvest (common with Argentine ADRs)."""
    try:
        info = getattr(yf_ticker, "info", {})
        if data.get("roe") is not None and abs(data["roe"]) > ANOMALY_THRESHOLD:
            yf_roe = info.get("returnOnEquity")
            data["roe"] = yf_roe * 100 if yf_roe is not None else None
            logger.info("Anomaly filter applied to ROE for %s", ticker)

        if data.get("roic") is not None and abs(data["roic"]) > ANOMALY_THRESHOLD:
            yf_roa = info.get("returnOnAssets")
            data["roic"] = yf_roa * 100 if yf_roa is not None else None
            logger.info("Anomaly filter applied to ROIC for %s", ticker)
    except Exception as e:
        logger.warning("Anomaly filter failed for %s: %s", ticker, e)


# --- Cache Read/Write Helpers (C2: DRY) ---

def _read_from_cache(ticker: str) -> Dict[str, Any] | None:
    """Reads parsed metrics from the database cache if still valid."""
    hours = _get_cache_hours()
    threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
    cached_record = ParsedMetricsCache.get_or_none(ParsedMetricsCache.ticker == ticker)

    if cached_record and cached_record.last_updated >= threshold:
        try:
            cached_data = json.loads(cached_record.data)
            if _is_valid_data(cached_data):
                return cached_data
        except Exception:
            logger.debug("Failed to deserialize cache for %s, will re-fetch", ticker)
    return None


def _write_to_cache(ticker: str, data: Dict[str, Any]) -> None:
    """Saves parsed metrics to the database cache (atomic upsert)."""
    if not _is_valid_data(data):
        return
    try:
        ParsedMetricsCache.replace(
            ticker=ticker,
            data=json.dumps(data),
            last_updated=datetime.datetime.now()
        ).execute()
    except Exception as e:
        logger.error("Cache save failed for %s: %s", ticker, e)


# --- Public API ---

def fetch_stock_metrics(ticker: str, is_us_reit: bool = False) -> Dict[str, Any]:
    """Fetches stock metrics into a unified dictionary format."""
    cached = _read_from_cache(ticker)
    if cached:
        return cached

    data = _init_empty_metrics(ticker)
    try:
        yf_ticker = yf.Ticker(ticker)
        info = getattr(yf_ticker, "info", {})
        fast_info = getattr(yf_ticker, "fast_info", None)

        # Determine price
        if fast_info and hasattr(fast_info, 'last_price'):
            data["price"] = fast_info.last_price
        else:
            data["price"] = info.get("currentPrice", info.get("regularMarketPrice"))

        data["name"] = info.get("shortName", ticker)

        # Persist Market Cap and P/S for valuation donut charts
        market_cap = info.get('marketCap')
        data["market_cap"] = market_cap
        ps_ratio = info.get('priceToSalesTrailing12Months')
        if ps_ratio is not None:
            data["p_s"] = round(float(ps_ratio), 2)

        # Compute P/A (Price-to-Assets = Market Cap / Total Assets)
        # Compute P/NWC (Price-to-Net Working Capital = Market Cap / (Current Assets - Current Liabilities))
        try:
            bs = yf_ticker.balance_sheet
            if hasattr(bs, 'index') and len(bs.columns) > 0:
                if 'Total Assets' in bs.index:
                    total_assets = bs.loc['Total Assets'].iloc[0]
                    if market_cap and total_assets and total_assets > 0:
                        data["p_a"] = round(float(market_cap / total_assets), 2)

                # Net Working Capital = Current Assets - Current Liabilities
                current_assets = None
                current_liabilities = None
                if 'Current Assets' in bs.index:
                    current_assets = bs.loc['Current Assets'].iloc[0]
                if 'Current Liabilities' in bs.index:
                    current_liabilities = bs.loc['Current Liabilities'].iloc[0]

                if current_assets is not None and current_liabilities is not None:
                    nwc = float(current_assets) - float(current_liabilities)
                    if market_cap and nwc > 0:
                        data["p_nwc"] = round(float(market_cap / nwc), 2)
        except Exception as e:
            logger.warning("P/A or P/NWC calculation failed for %s: %s", ticker, e)

        # Primary source for fundamentals (P/E, EPS, ROE, etc.)
        _populate_yfinance_fundamentals(data, info)

        # StatusInvest can override with its own values when available
        is_br = ticker.endswith(".SA")
        if is_br:
            _get_statusinvest_data(ticker, data, is_br=True)
        else:
            _get_statusinvest_data(ticker, data, is_br=False, is_us_reit=is_us_reit)
            _apply_anomaly_filter(ticker, data, yf_ticker)

        _compute_ttm_fcf(ticker, data, yf_ticker)
    except Exception as e:
        logger.error("Failed to fetch stock metrics for %s: %s", ticker, e)

    _write_to_cache(ticker, data)
    return data


def _fetch_reit_yfinance(ticker: str, data: Dict[str, Any]) -> None:
    """Fetches FII/REIT core metrics from yfinance (primary source)."""
    try:
        yf_ticker = yf.Ticker(ticker)
        info = getattr(yf_ticker, "info", {})
        fast_info = getattr(yf_ticker, "fast_info", None)

        # Price
        if fast_info and hasattr(fast_info, 'last_price'):
            data["price"] = fast_info.last_price
        else:
            data["price"] = info.get("currentPrice", info.get("regularMarketPrice"))

        data["name"] = info.get("shortName", ticker)

        # Dividend Yield — yfinance returns percentage for BR FIIs (e.g. 9.47)
        dy = info.get("dividendYield")
        if dy is not None:
            data["dividend_yield"] = float(dy)

        # P/VP (Price to Book)
        ptb = info.get("priceToBook")
        if ptb is not None:
            data["p_vpa"] = round(float(ptb), 4)

        # 52-week range
        data["min_52w"] = info.get("fiftyTwoWeekLow")
        data["max_52w"] = info.get("fiftyTwoWeekHigh")

        # Val 12M — calculated from 1-year price history
        try:
            hist = yf_ticker.history(period="1y")
            if hist is not None and not hist.empty and len(hist) >= 2:
                first_close = float(hist["Close"].iloc[0])
                last_close = float(hist["Close"].iloc[-1])
                if first_close > 0:
                    data["val_12m"] = round(((last_close - first_close) / first_close) * 100, 2)
        except Exception as e:
            logger.debug("Val 12M calculation failed for %s: %s", ticker, e)

        # Book value per share (VP/Cota)
        bv = info.get("bookValue")
        if bv is not None:
            data["vp_cota"] = float(bv)

    except Exception as e:
        logger.error("yfinance fetch failed for REIT %s: %s", ticker, e)


def _fetch_reit_statusinvest_extras(ticker: str, data: Dict[str, Any]) -> None:
    """Fallback: fetches StatusInvest-exclusive fields (dy_cagr, val_cagr, caixa, cotistas).

    Non-critical — silently skips if StatusInvest is blocked or unavailable.
    """
    try:
        statusinvest_ticker = ticker.replace(".SA", "").upper()
        headers = STATUS_INVEST_HEADERS
        categories = FII_CATEGORIES

        for category in categories:
            url = f'https://statusinvest.com.br/{category}/{statusinvest_ticker.lower()}'
            response = _get_session().get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                name_tag = soup.find('h1')
                if name_tag and name_tag.text.strip():
                    if 'erro' in name_tag.text.lower() or 'não encontram' in name_tag.text.lower() or 'ops' in name_tag.text.lower():
                        continue

                    for title in soup.find_all('h3', class_='title'):
                        val_tag = title.find_next('strong', class_='value')
                        if val_tag:
                            label_text = title.text.strip().lower()
                            parsed_value = _parse_brazilian_currency(val_tag.text.strip())
                            # Only scrape fields that yfinance doesn't provide
                            if 'dy cagr (3 anos)' in label_text: data['dy_cagr'] = parsed_value
                            elif 'valor cagr (3 anos)' in label_text: data['val_cagr'] = parsed_value
                            elif 'valor em caixa' in label_text: data['caixa'] = parsed_value
                            elif 'cotistas' in label_text: data['cotistas'] = int(parsed_value) if parsed_value else None

                    break  # Found the right category page
    except Exception as e:
        logger.debug("StatusInvest extras unavailable for %s: %s", ticker, e)


def fetch_reit_metrics(ticker: str) -> Dict[str, Any]:
    """Fetches FII/REIT metrics using yfinance (primary) with StatusInvest fallback for extras."""
    cached = _read_from_cache(ticker)
    if cached:
        return cached

    data = _init_empty_metrics(ticker)

    # Primary source: yfinance (price, DY, P/VP, 52W, val_12m, vp_cota)
    _fetch_reit_yfinance(ticker, data)

    # Fallback: StatusInvest-exclusive fields (dy_cagr, val_cagr, caixa, cotistas)
    _fetch_reit_statusinvest_extras(ticker, data)

    _write_to_cache(ticker, data)
    return data
