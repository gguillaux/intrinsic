"""
Data providers package using Strategy design pattern.
"""
from .base import MetricsProvider
from .yfinance_provider import YFinanceProvider, resolve_price, populate_fundamentals, compute_ttm_fcf

def get_session(): pass
def update_cache_expiration(hours): pass

__all__ = [
    "MetricsProvider",
    "YFinanceProvider",
    "resolve_price",
    "populate_fundamentals",
    "compute_ttm_fcf",
    "get_session",
    "update_cache_expiration",
]
