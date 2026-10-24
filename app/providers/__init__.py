"""
Data providers package using Strategy design pattern.
"""
from .base import MetricsProvider
from .yfinance_provider import (
    YFinanceProvider,
    resolve_price,
    populate_fundamentals,
    compute_ttm_fcf,
    compute_dividend_cagr,
    clean_price_series,
)
from .fundamentus_provider import FundamentusProvider

def get_session(): pass
def update_cache_expiration(hours): pass

__all__ = [
    "MetricsProvider",
    "YFinanceProvider",
    "FundamentusProvider",
    "resolve_price",
    "populate_fundamentals",
    "compute_ttm_fcf",
    "compute_dividend_cagr",
    "clean_price_series",
    "get_session",
    "update_cache_expiration",
]
