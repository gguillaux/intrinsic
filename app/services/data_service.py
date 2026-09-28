"""
Data Service — Orchestrates data retrieval using Strategy pattern providers,
caching results in SQLite.
"""
import logging
import json
import datetime
from typing import Dict, Any, List, Optional

from ..models import ParsedMetricsCache
from ..config import DEFAULT_CACHE_HOURS
from ..domain.models import StockMetrics
from ..providers import (
    MetricsProvider,
    YFinanceProvider,
    get_session as _get_session_impl,
    update_cache_expiration as _update_cache_expiration_impl,
    populate_fundamentals,
    compute_ttm_fcf as _compute_ttm_fcf_impl,
)

logger = logging.getLogger(__name__)

_cache_hours: int = DEFAULT_CACHE_HOURS
_providers: List[MetricsProvider] = [
    YFinanceProvider(),
]


def get_providers() -> List[MetricsProvider]:
    """Returns registered providers sorted by priority."""
    return sorted(_providers, key=lambda p: p.priority)


def register_provider(provider: MetricsProvider) -> None:
    """Allows dynamic registration of alternative providers."""
    _providers.append(provider)


# Backward compatibility aliases
_get_session = _get_session_impl
_populate_yfinance_fundamentals = populate_fundamentals
_compute_ttm_fcf = _compute_ttm_fcf_impl


def update_cache_expiration(hours: int) -> None:
    """Updates HTTP session cache and local service cache hours."""
    global _cache_hours
    _cache_hours = hours
    _update_cache_expiration_impl(hours)


def _get_cache_hours() -> int:
    return _cache_hours


def _is_valid_data(data: Dict[str, Any]) -> bool:
    return data.get("price") is not None


def _init_empty_metrics(ticker: str) -> Dict[str, Any]:
    return StockMetrics(ticker=ticker, name=ticker).to_dict()


# --- Database Cache Helpers ---

def _read_from_cache(ticker: str) -> Optional[Dict[str, Any]]:
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
    """Fetches stock metrics by chaining registered providers in priority order."""
    cached = _read_from_cache(ticker)
    if cached:
        return cached

    data = _init_empty_metrics(ticker)
    for provider in get_providers():
        try:
            provider.fetch_stock(ticker, data, is_us_reit=is_us_reit)
        except Exception as e:
            logger.warning("Provider %s failed for stock %s: %s", provider.name, ticker, e)

    _write_to_cache(ticker, data)
    return data


def fetch_reit_metrics(ticker: str) -> Dict[str, Any]:
    """Fetches REIT metrics by chaining registered providers in priority order."""
    cached = _read_from_cache(ticker)
    if cached:
        return cached

    data = _init_empty_metrics(ticker)
    for provider in get_providers():
        try:
            provider.fetch_reit(ticker, data)
        except Exception as e:
            logger.warning("Provider %s failed for REIT %s: %s", provider.name, ticker, e)

    _write_to_cache(ticker, data)
    return data
