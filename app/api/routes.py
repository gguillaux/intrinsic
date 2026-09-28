import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..adapters.factories import DataProviderFactory, ValuationEngineFactory
from ..core.entities import Stock
from ..use_cases.diligence import CalculateZScoreUseCase, ROICCalculator

# Legacy imports for frontend table views
from ..services.data_service import fetch_stock_metrics, fetch_reit_metrics, update_cache_expiration
from ..domain.calculations import calculate_ranking, enrich_fii_metrics
from ..services.index_service import get_index_composition
from ..services.news_service import fetch_and_store_news
from ..models import ParsedMetricsCache

logger = logging.getLogger(__name__)
router = APIRouter()

# --- NEW Clean Architecture Endpoint ---
@router.get("/valuation/{ticker}")
async def get_valuation(ticker: str, sector: str = "Industrial"):
    """
    Evaluates the intrinsic value of a given ticker using the appropriate 
    data provider (US vs BR) and strategy (DCF vs DDM).
    """
    try:
        ticker = ticker.upper()
        
        # 1. Instantiate Providers
        fund_provider = DataProviderFactory.get_fundamentals_provider(ticker)
        price_provider = DataProviderFactory.get_pricing_provider()
        
        # 2. Fetch Data
        pricing_data = price_provider.fetch_realtime_pricing(ticker)
        statements = fund_provider.fetch_fundamentals(ticker)
        
        if not statements:
            raise HTTPException(status_code=404, detail="No financial statements found.")
            
        latest_statement = statements[-1]
            
        # 3. Assemble Domain Entity
        stock = Stock(
            ticker=ticker,
            exchange="B3" if ticker.endswith(".SA") else "US",
            sector=sector,
            current_price=pricing_data.get('current_price', 0.0),
            beta=pricing_data.get('beta', 1.0),
            market_cap=pricing_data.get('market_cap', 0.0),
            historical_statements=statements
        )
        
        # 4. Solvency Diagnostics
        z_score = CalculateZScoreUseCase.execute(latest_statement, stock.market_cap)
        roic = ROICCalculator.execute(latest_statement)
        is_distressed = z_score < 1.8 if z_score > 0 else False
        
        # 5. Execute Valuation Strategy
        strategy = ValuationEngineFactory.get_strategy(stock.sector, stock.exchange)
        result = strategy.calculate_intrinsic_value(stock)
        
        # Enrich result with diagnostics
        result.z_score = z_score
        result.roic_3yr_avg = roic
        result.is_distressed = is_distressed
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Valuation failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- LEGACY Endpoints for Frontend Table Views ---

def parse_tickers(tickers: str) -> List[str]:
    if not tickers:
        return []
    return [t.strip().upper() for t in tickers.split(",") if t.strip()]

@router.get("/stocks/br")
async def get_br_stocks(tickers: Optional[str] = None, index: Optional[str] = "IBOV"):
    asset_list = parse_tickers(tickers)
    if not asset_list and index:
        composition = get_index_composition(index)
        asset_list = [c["ticker"] for c in composition]
    
    if not asset_list:
        asset_list = ["VALE3.SA", "PETR4.SA", "ITUB4.SA"] # Default fallback
        
    results = []
    for ticker in asset_list:
        if not ticker.endswith(".SA"):
            ticker += ".SA"
        res = fetch_stock_metrics(ticker)
        if res:
            results.append(res)
    return calculate_ranking(results, 'stock')

@router.get("/stocks/us")
async def get_us_stocks(tickers: Optional[str] = None):
    asset_list = parse_tickers(tickers)
    if not asset_list:
        asset_list = ["AAPL", "MSFT", "GOOGL"]
        
    results = []
    for ticker in asset_list:
        res = fetch_stock_metrics(ticker, is_us_reit=False)
        if res:
            results.append(res)
    return calculate_ranking(results, 'stock')

@router.get("/fiis/br")
async def get_br_fiis(
    tickers: Optional[str] = None, 
    ntnb: float = 6.0, 
    spread: float = 4.0, 
    selic: float = 10.5
):
    asset_list = parse_tickers(tickers)
    if not asset_list:
        asset_list = ["HGLG11.SA", "MXRF11.SA", "KNRI11.SA"]
        
    results = []
    for ticker in asset_list:
        if not ticker.endswith(".SA"):
            ticker += ".SA"
        res = fetch_reit_metrics(ticker)
        if res:
            results.append(res)
    return enrich_fii_metrics(results, ntnb_rate=ntnb, spread=spread, selic_rate=selic)

@router.get("/reits/us")
async def get_us_reits(tickers: Optional[str] = None):
    asset_list = parse_tickers(tickers)
    if not asset_list:
        asset_list = ["O", "AMT", "PLD"]
        
    results = []
    for ticker in asset_list:
        res = fetch_stock_metrics(ticker, is_us_reit=True)
        if res:
            results.append(res)
    return calculate_ranking(results, 'stock')

@router.get("/news")
async def get_news(date: Optional[str] = None):
    return fetch_and_store_news(date)

class CacheConfigRequest(BaseModel):
    hours: int

@router.post("/cache/config")
async def update_cache_config(req: CacheConfigRequest):
    update_cache_expiration(req.hours)
    return {"status": "success", "cache_hours": req.hours}

@router.post("/cache/clear")
async def clear_cache():
    ParsedMetricsCache.delete().execute()
    return {"status": "success", "message": "Cache cleared"}
