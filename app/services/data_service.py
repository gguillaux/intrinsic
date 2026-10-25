import logging
import json
import datetime
import time
import concurrent.futures
from typing import Dict, Any, List, Optional

from ..models import ParsedMetricsCache
from ..config import DEFAULT_CACHE_HOURS
from ..domain.models import StockMetrics
from ..providers import (
    MetricsProvider,
    YFinanceProvider,
    FundamentusProvider,
    get_session as _get_session_impl,
    update_cache_expiration as _update_cache_expiration_impl,
    populate_fundamentals,
    compute_ttm_fcf as _compute_ttm_fcf_impl,
)

logger = logging.getLogger(__name__)

_cache_hours: int = DEFAULT_CACHE_HOURS
_providers: List[MetricsProvider] = [
    YFinanceProvider(),      # priority 10 — prices, dividend history (Div. CAGR)
    FundamentusProvider(),   # priority 20 — BR FII fundamentals (P/VP, FFO Yield, VP/Cota...)
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
    return data.get("price") is not None and not data.get("_error")


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
            if cached_data.get("_error"):
                # Negative cache hit — do not re-request dead/delisted tickers
                return cached_data
        except Exception:
            logger.debug("Failed to deserialize cache for %s, will re-fetch", ticker)
    return None


def _write_to_cache(ticker: str, data: Dict[str, Any]) -> None:
    """Saves parsed metrics to the database cache (atomic upsert), supporting negative caching."""
    if not _is_valid_data(data):
        payload = {"ticker": ticker, "name": ticker, "_error": True}
    else:
        payload = data
    try:
        ParsedMetricsCache.replace(
            ticker=ticker,
            data=json.dumps(payload),
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

    start = time.monotonic()
    data = _init_empty_metrics(ticker)
    for provider in get_providers():
        try:
            provider.fetch_stock(ticker, data, is_us_reit=is_us_reit)
        except Exception as e:
            logger.warning("Provider %s failed for stock %s: %s", provider.name, ticker, e)

    _write_to_cache(ticker, data)
    elapsed = time.monotonic() - start
    logger.info("Fetched stock %s in %.2fs (valid=%s)", ticker, elapsed, data.get("price") is not None)
    return data


def fetch_reit_metrics(ticker: str) -> Dict[str, Any]:
    """Fetches REIT metrics by chaining registered providers in priority order."""
    cached = _read_from_cache(ticker)
    if cached:
        return cached

    start = time.monotonic()
    data = _init_empty_metrics(ticker)
    for provider in get_providers():
        try:
            provider.fetch_reit(ticker, data)
        except Exception as e:
            logger.warning("Provider %s failed for REIT %s: %s", provider.name, ticker, e)

    _write_to_cache(ticker, data)
    elapsed = time.monotonic() - start
    logger.info("Fetched REIT %s in %.2fs (valid=%s)", ticker, elapsed, data.get("price") is not None)
    return data


def fetch_many_stocks(
    tickers: List[str],
    is_us_reit: bool = False,
    max_workers: int = 8,
    fetch_fn = None
) -> List[Dict[str, Any]]:
    """Fetches metrics for multiple stocks concurrently, preserving input order."""
    if not tickers:
        return []

    fn = fetch_fn or fetch_stock_metrics
    results_map: Dict[str, Dict[str, Any]] = {}
    uncached: List[str] = []

    for t in tickers:
        cached = _read_from_cache(t)
        if cached:
            results_map[t] = cached
        else:
            uncached.append(t)

    if uncached:
        workers = min(max_workers, len(uncached))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_ticker = {
                executor.submit(fn, t, is_us_reit) if fn is fetch_stock_metrics else executor.submit(fn, t): t
                for t in uncached
            }
            for future in concurrent.futures.as_completed(future_to_ticker):
                t = future_to_ticker[future]
                try:
                    res = future.result()
                    if res:
                        results_map[t] = res
                except Exception as e:
                    logger.error("Error fetching stock %s in parallel: %s", t, e)

    valid_results = []
    for t in tickers:
        res = results_map.get(t)
        if res and not res.get("_error") and res.get("price") is not None:
            valid_results.append(dict(res))
    return valid_results


def fetch_many_reits(
    tickers: List[str],
    max_workers: int = 8,
    fetch_fn = None
) -> List[Dict[str, Any]]:
    """Fetches metrics for multiple REITs concurrently, preserving input order."""
    if not tickers:
        return []

    fn = fetch_fn or fetch_reit_metrics
    results_map: Dict[str, Dict[str, Any]] = {}
    uncached: List[str] = []

    for t in tickers:
        cached = _read_from_cache(t)
        if cached:
            results_map[t] = cached
        else:
            uncached.append(t)

    if uncached:
        workers = min(max_workers, len(uncached))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_ticker = {
                executor.submit(fn, t): t
                for t in uncached
            }
            for future in concurrent.futures.as_completed(future_to_ticker):
                t = future_to_ticker[future]
                try:
                    res = future.result()
                    if res:
                        results_map[t] = res
                except Exception as e:
                    logger.error("Error fetching REIT %s in parallel: %s", t, e)

    valid_results = []
    for t in tickers:
        res = results_map.get(t)
        if res and not res.get("_error") and res.get("price") is not None:
            valid_results.append(dict(res))
    return valid_results

