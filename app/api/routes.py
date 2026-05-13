import logging
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
import requests_cache

from ..config import DEFAULT_BR_STOCKS, DEFAULT_US_STOCKS, DEFAULT_BR_FIIS, DEFAULT_US_REITS
from ..services.data_service import fetch_stock_metrics, fetch_reit_metrics, update_cache_expiration
from ..services.news_service import fetch_and_store_news
from ..services.index_service import get_all_indices, get_index_composition
from ..domain.calculations import calculate_ranking, enrich_fii_metrics
from ..models import ParsedMetricsCache

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Response Schema ---

class ValuationMetricSchema(BaseModel):
    ticker: str
    name: Optional[str] = None
    price: Optional[float] = None
    p_fcf: Optional[float] = None
    pe: Optional[float] = None
    eps: Optional[float] = None
    debt_ebit: Optional[float] = None
    roic: Optional[float] = None
    roe: Optional[float] = None
    net_margin: Optional[float] = None
    peg: Optional[float] = None
    dividend_yield: Optional[float] = None
    p_vpa: Optional[float] = None
    min_52w: Optional[float] = None
    max_52w: Optional[float] = None
    val_12m: Optional[float] = None
    vp_cota: Optional[float] = None
    caixa: Optional[float] = None
    dy_cagr: Optional[float] = None
    val_cagr: Optional[float] = None
    cotistas: Optional[int] = None
    ceiling_price: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    rank_score: Optional[float] = None
    final_rank: Optional[int] = None


# --- Ticker Parsing Helpers (C3: DRY) ---

def _parse_ticker_list(raw: Optional[str], defaults: List[str], append_sa: bool = False) -> List[str]:
    """Parses a comma-separated ticker string, falling back to defaults."""
    if not raw:
        return defaults
    tickers = [t.strip().upper() for t in raw.split(",") if t.strip()]
    if append_sa:
        tickers = [t if t.endswith(".SA") else t + ".SA" for t in tickers]
    return tickers


async def _fetch_parallel(fetch_fn, ticker_list: List[str], **kwargs) -> List[dict]:
    """Runs a fetch function in parallel across a list of tickers."""
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, lambda t=t: fetch_fn(t, **kwargs)) for t in ticker_list]
    return list(await asyncio.gather(*tasks))


# --- Equity Endpoints ---

@router.get("/stocks/br")
async def get_br_stocks(index: str = "IBOV", tickers: Optional[str] = None):
    if tickers:
        ticker_list = _parse_ticker_list(tickers, DEFAULT_BR_STOCKS, append_sa=True)
    else:
        comp = get_index_composition(index)
        ticker_list = [item["ticker"] for item in comp] if comp else DEFAULT_BR_STOCKS

    results = await _fetch_parallel(fetch_stock_metrics, ticker_list)
    return calculate_ranking(results, 'stock')


@router.get("/stocks/us")
async def get_us_stocks(tickers: Optional[str] = None):
    ticker_list = _parse_ticker_list(tickers, DEFAULT_US_STOCKS)
    results = await _fetch_parallel(fetch_stock_metrics, ticker_list)
    return calculate_ranking(results, 'stock')


# --- Real Estate Endpoints ---

@router.get("/fiis/br")
async def get_br_fiis(
    tickers: Optional[str] = None,
    ntnb: float = 6.0,
    spread: float = 4.0,
    selic: float = 10.5,
):
    ticker_list = _parse_ticker_list(tickers, DEFAULT_BR_FIIS)
    results = await _fetch_parallel(fetch_reit_metrics, ticker_list)
    return enrich_fii_metrics(results, ntnb_rate=ntnb, spread=spread, selic_rate=selic)


@router.get("/reits/us")
async def get_us_reits(tickers: Optional[str] = None):
    ticker_list = _parse_ticker_list(tickers, DEFAULT_US_REITS)
    results = await _fetch_parallel(fetch_stock_metrics, ticker_list, is_us_reit=True)
    return results


# --- News & Index Endpoints ---

@router.get("/news")
async def get_news(date: Optional[str] = None):
    return fetch_and_store_news(date)


@router.get("/indices")
async def list_indices():
    return get_all_indices()


@router.get("/indices/{index_name}")
async def get_index(index_name: str):
    return get_index_composition(index_name)


# --- Cache Management Endpoints ---

@router.post("/cache/clear")
async def clear_cache():
    try:
        session = requests_cache.CachedSession('intrinsic_statusinvest.cache')
        session.cache.clear()
        ParsedMetricsCache.delete().execute()
        logger.info("Cache cleared successfully")
        return {"status": "Cache Cleared"}
    except Exception as e:
        logger.error("Failed to clear cache", exc_info=True)
        return {"status": "Error", "message": str(e)}


class CacheConfig(BaseModel):
    hours: int

@router.post("/cache/config")
async def config_cache(config: CacheConfig):
    try:
        update_cache_expiration(config.hours)
        return {"status": "Cache Updated", "hours": config.hours}
    except Exception as e:
        logger.error("Failed to update cache config", exc_info=True)
        return {"status": "Error", "message": str(e)}
