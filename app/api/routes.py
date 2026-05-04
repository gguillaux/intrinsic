from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel
import asyncio
from ..services.data_service import fetch_stock_metrics, fetch_reit_metrics

router = APIRouter()

class ValuationMetric(BaseModel):
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

# Pre-defined list of tickers to fetch (could be dynamic or from DB in the future)
BR_STOCKS = ["ABEV3.SA", "ITUB4.SA", "WEGE3.SA", "VALE3.SA"]
US_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA"]
BR_FIIS = ["HGLG11.SA", "MXRF11.SA", "KNRI11.SA", "XPLG11.SA"]
US_REITS = ["O", "SPG", "PLD", "VNQ"]

@router.get("/stocks/br", response_model=List[ValuationMetric])
async def get_br_stocks(index: str = "IBOV", tickers: Optional[str] = None):
    # Run synchronously in threadpool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    if tickers:
        ticker_list = []
        for t in tickers.split(","):
            t = t.strip().upper()
            if t:
                if not t.endswith(".SA"):
                    t += ".SA"
                ticker_list.append(t)
    else:
        comp = get_index_composition(index)
        if comp:
            ticker_list = [item["ticker"] for item in comp]
        else:
            ticker_list = BR_STOCKS
    tasks = [loop.run_in_executor(None, fetch_stock_metrics, t) for t in ticker_list]
    results = await asyncio.gather(*tasks)
    return results

@router.get("/stocks/us", response_model=List[ValuationMetric])
async def get_us_stocks(tickers: Optional[str] = None):
    loop = asyncio.get_event_loop()
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    else:
        ticker_list = US_STOCKS
    tasks = [loop.run_in_executor(None, fetch_stock_metrics, t) for t in ticker_list]
    results = await asyncio.gather(*tasks)
    return results

@router.get("/fiis/br", response_model=List[ValuationMetric])
async def get_br_fiis(tickers: Optional[str] = None):
    loop = asyncio.get_event_loop()
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    else:
        ticker_list = BR_FIIS
    tasks = [loop.run_in_executor(None, fetch_reit_metrics, t) for t in ticker_list]
    results = await asyncio.gather(*tasks)
    return results

@router.get("/reits/us", response_model=List[ValuationMetric])
async def get_us_reits(tickers: Optional[str] = None):
    loop = asyncio.get_event_loop()
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    else:
        ticker_list = US_REITS
    
    # Run fetch_stock_metrics with is_us_reit=True
    tasks = [loop.run_in_executor(None, fetch_stock_metrics, t, True) for t in ticker_list]
    results = await asyncio.gather(*tasks)
    return results

# --- New V2 Endpoints ---

from ..services.news_service import fetch_and_store_news
from ..services.index_service import get_all_indices, get_index_composition

@router.get("/news")
async def get_news(date: Optional[str] = None):
    # Feeds from DB cache or fresh scrape
    return fetch_and_store_news(date)

@router.get("/indices")
async def list_indices():
    return get_all_indices()

@router.get("/indices/{index_name}")
async def get_index(index_name: str):
    return get_index_composition(index_name)

import os
import requests_cache
@router.post("/cache/clear")
async def clear_cache():
    try:
        session = requests_cache.CachedSession('intrinsic_statusinvest.cache')
        session.cache.clear()
        
        if os.path.exists("data.db"):
            os.remove("data.db")
        from ..database import init_db
        init_db()
        return {"status": "Cache Cleared"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

class CacheConfig(BaseModel):
    hours: int

@router.post("/cache/config")
async def config_cache(config: CacheConfig):
    from ..services.data_service import update_cache_expiration
    try:
        update_cache_expiration(config.hours)
        return {"status": "Cache Updated", "hours": config.hours}
    except Exception as e:
        return {"status": "Error", "message": str(e)}
