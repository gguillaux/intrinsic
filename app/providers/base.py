"""
Abstract Strategy base class for data providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class MetricsProvider(ABC):
    """Strategy interface for financial metrics data providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Execution priority (lower numbers run first)."""
        pass

    @abstractmethod
    def fetch_stock(self, ticker: str, data: Dict[str, Any], **kwargs) -> None:
        """Populate or enrich data dictionary with stock metrics. Should not raise."""
        pass

    @abstractmethod
    def fetch_reit(self, ticker: str, data: Dict[str, Any], **kwargs) -> None:
        """Populate or enrich data dictionary with REIT metrics. Should not raise."""
        pass
