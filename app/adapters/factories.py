from ..infrastructure.providers import EdgarToolsDataProvider, BrFinanceDataProvider, YahooFinanceDataProvider
from ..core.interfaces import IStockDataProvider, IValuationStrategy
from ..use_cases.valuation import CalculateDCFUseCase, CalculateDDMUseCase

class DataProviderFactory:
    @staticmethod
    def get_fundamentals_provider(ticker: str) -> IStockDataProvider:
        """Routes US tickers to edgartools, BR tickers to brfinance_v2."""
        if ticker.endswith(".SA"):
            return BrFinanceDataProvider()
        return EdgarToolsDataProvider()
        
    @staticmethod
    def get_pricing_provider() -> YahooFinanceDataProvider:
        """Returns the real-time pricing provider (always yfinance)."""
        return YahooFinanceDataProvider()


class ValuationEngineFactory:
    @staticmethod
    def get_strategy(sector: str, exchange: str = "US") -> IValuationStrategy:
        """
        Dynamically returns the appropriate valuation strategy.
        FIIs, REITs, and Banks get DDM. Mature industrials get DCF.
        """
        sector = sector.upper()
        if "REIT" in sector or "FII" in sector or "FINANCIAL" in sector or "BANK" in sector:
            return CalculateDDMUseCase()
        else:
            return CalculateDCFUseCase(iterations=10000)
