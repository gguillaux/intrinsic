"""
StatusInvest data provider strategy implementation.
"""
import logging
import threading
import datetime
from datetime import timedelta
from typing import Dict, Any, Optional

import yfinance as yf
import requests_cache
from bs4 import BeautifulSoup

from .base import MetricsProvider
from ..config import (
    REQUEST_TIMEOUT,
    ANOMALY_THRESHOLD,
    STATUS_INVEST_HEADERS,
    STATUSINVEST_INDICATOR_MAPPING,
    DEFAULT_CACHE_HOURS,
    FII_CATEGORIES,
)

logger = logging.getLogger(__name__)

# --- Thread-safe cached session ---
_session_lock = threading.Lock()
_status_invest_session: Optional[requests_cache.CachedSession] = None
_cache_hours: int = DEFAULT_CACHE_HOURS


def get_session() -> requests_cache.CachedSession:
    """Returns the thread-safe cached session singleton."""
    global _status_invest_session
    with _session_lock:
        if _status_invest_session is None:
            _status_invest_session = requests_cache.CachedSession(
                'intrinsic_statusinvest.cache',
                expire_after=timedelta(hours=_cache_hours)
            )
        return _status_invest_session


def update_cache_expiration(hours: int) -> None:
    """Updates the HTTP cache session expiration."""
    global _status_invest_session, _cache_hours
    with _session_lock:
        _cache_hours = hours
        _status_invest_session = requests_cache.CachedSession(
            'intrinsic_statusinvest.cache',
            expire_after=timedelta(hours=hours)
        )


def parse_brazilian_currency(text: str) -> Optional[float]:
    """Parses Brazilian-formatted numbers (e.g. 'R$ 1.234,56' or '12,34%') to float."""
    if not text or text == '-':
        return None
    cleaned = text.replace('%', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def apply_anomaly_filter(ticker: str, data: Dict[str, Any]) -> None:
    """Filters out hyperinflated metrics from StatusInvest (e.g. Argentine ADRs)."""
    try:
        if (data.get("roe") is not None and abs(data["roe"]) > ANOMALY_THRESHOLD) or \
           (data.get("roic") is not None and abs(data["roic"]) > ANOMALY_THRESHOLD):
            yf_ticker = yf.Ticker(ticker)
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


class StatusInvestProvider(MetricsProvider):
    """Secondary data provider using StatusInvest (with Cloudflare fallback safety)."""

    @property
    def name(self) -> str:
        return "statusinvest"

    @property
    def priority(self) -> int:
        return 20

    def fetch_stock(self, ticker: str, data: Dict[str, Any], is_us_reit: bool = False, **kwargs) -> None:
        statusinvest_ticker = ticker.replace(".SA", "").replace(".sa", "").upper()
        is_br = ticker.endswith(".SA")
        try:
            url_path = 'acao' if is_br else ('reit' if is_us_reit else 'stock')
            url = f'https://statusinvest.com.br/{url_path}/indicatorhistoricallist'
            payload = {'codes[]': statusinvest_ticker, 'time': '7', 'byQuarter': 'false', 'futureData': 'false'}

            response = get_session().post(url, data=payload, headers=STATUS_INVEST_HEADERS, timeout=REQUEST_TIMEOUT)
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

            if not is_br:
                apply_anomaly_filter(ticker, data)

        except Exception as e:
            logger.warning("StatusInvest fetch failed for %s: %s", ticker, e)

    def fetch_reit(self, ticker: str, data: Dict[str, Any], **kwargs) -> None:
        """Fetches StatusInvest-exclusive FII fields (dy_cagr, val_cagr, caixa, cotistas)."""
        try:
            statusinvest_ticker = ticker.replace(".SA", "").upper()
            headers = STATUS_INVEST_HEADERS

            for category in FII_CATEGORIES:
                url = f'https://statusinvest.com.br/{category}/{statusinvest_ticker.lower()}'
                response = get_session().get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    name_tag = soup.find('h1')
                    if name_tag and name_tag.text.strip():
                        if any(term in name_tag.text.lower() for term in ['erro', 'não encontram', 'ops']):
                            continue

                        for title in soup.find_all('h3', class_='title'):
                            val_tag = title.find_next('strong', class_='value')
                            if val_tag:
                                label_text = title.text.strip().lower()
                                parsed_value = parse_brazilian_currency(val_tag.text.strip())
                                if 'dy cagr (3 anos)' in label_text:
                                    data['dy_cagr'] = parsed_value
                                elif 'valor cagr (3 anos)' in label_text:
                                    data['val_cagr'] = parsed_value
                                elif 'valor em caixa' in label_text:
                                    data['caixa'] = parsed_value
                                elif 'cotistas' in label_text:
                                    data['cotistas'] = int(parsed_value) if parsed_value else None

                        break  # Page found and processed
        except Exception as e:
            logger.debug("StatusInvest extras unavailable for %s: %s", ticker, e)
