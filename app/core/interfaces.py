from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Stock, FinancialStatement, ValuationResult

class IStockDataProvider(ABC):
    @abstractmethod
    def fetch_fundamentals(self, ticker: str) -> List[FinancialStatement]:
        """Fetches historical financial statements."""
        pass
        
    @abstractmethod
    def fetch_realtime_pricing(self, ticker: str) -> dict:
        """Fetches current price, beta, and market cap."""
        pass

class IValuationStrategy(ABC):
    @abstractmethod
    def calculate_intrinsic_value(self, stock: Stock, **kwargs) -> ValuationResult:
        """Calculates the intrinsic value of a given stock."""
        pass
