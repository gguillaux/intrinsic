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
    fcf: Optional[float] = None
    eps: Optional[float] = None
    debt: Optional[float] = None
    pe: Optional[float] = None
    peg: Optional[float] = None
    dividend_yield: Optional[float] = None
    p_vpa: Optional[float] = None

# Pre-defined list of tickers to fetch (could be dynamic or from DB in the future)
BR_STOCKS = ["ABEV3.SA", "ITUB4.SA", "WEGE3.SA", "VALE3.SA"]
US_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA"]
BR_FIIS = ["HGLG11.SA", "MXRF11.SA", "KNRI11.SA", "XPLG11.SA"]
US_REITS = ["O", "SPG", "PLD", "VNQ"]

@router.get("/stocks/br", response_model=List[ValuationMetric])
async def get_br_stocks():
    # Run synchronously in threadpool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, fetch_stock_metrics, t) for t in BR_STOCKS]
    results = await asyncio.gather(*tasks)
    return results

@router.get("/stocks/us", response_model=List[ValuationMetric])
async def get_us_stocks():
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, fetch_stock_metrics, t) for t in US_STOCKS]
    results = await asyncio.gather(*tasks)
    return results

@router.get("/fiis/br", response_model=List[ValuationMetric])
async def get_br_fiis():
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, fetch_reit_metrics, t) for t in BR_FIIS]
    results = await asyncio.gather(*tasks)
    return results

@router.get("/reits/us", response_model=List[ValuationMetric])
async def get_us_reits():
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, fetch_reit_metrics, t) for t in US_REITS]
    results = await asyncio.gather(*tasks)
    return results
