import pytest
from app.core.entities import Stock, FinancialStatement
from app.use_cases.valuation import CalculateDCFUseCase, CalculateDDMUseCase
from app.adapters.factories import DataProviderFactory, ValuationEngineFactory

def test_dcf_valuation_with_monte_carlo():
    strategy = CalculateDCFUseCase(iterations=100) # smaller iterations for test speed
    stock = Stock(
        ticker="AAPL",
        exchange="US",
        sector="Technology",
        current_price=150.0,
        historical_statements=[
            FinancialStatement(
                ticker="AAPL", year=2023, free_cash_flow=100000.0, shares_outstanding=1000
            )
        ]
    )
    result = strategy.calculate_intrinsic_value(stock, growth_rate=0.05, terminal_growth_rate=0.02, discount_rate=0.10)
    
    assert result.strategy_used == "DCF with Monte Carlo"
    assert len(result.scenarios) == 3
    assert result.probability_density is not None

def test_ddm_valuation_for_fii():
    strategy = CalculateDDMUseCase()
    stock = Stock(
        ticker="HGLG11.SA",
        exchange="B3",
        sector="FII",
        current_price=160.0
    )
    result = strategy.calculate_intrinsic_value(stock, expected_dividend=15.0, discount_rate=0.12, growth_rate=0.02)
    
    assert result.strategy_used == "Dividend Discount Model"
    assert len(result.scenarios) == 1
    assert result.scenarios[0].intrinsic_value == 150.0 # 15 / (0.12 - 0.02)

def test_factory_routing():
    # US Stock
    us_provider = DataProviderFactory.get_fundamentals_provider("AAPL")
    assert type(us_provider).__name__ == "EdgarToolsDataProvider"
    
    # BR Stock
    br_provider = DataProviderFactory.get_fundamentals_provider("PETR4.SA")
    assert type(br_provider).__name__ == "BrFinanceDataProvider"
    
    # Strategy Routing
    fii_strategy = ValuationEngineFactory.get_strategy("FII", "B3")
    assert type(fii_strategy).__name__ == "CalculateDDMUseCase"
    
    industrial_strategy = ValuationEngineFactory.get_strategy("Industrial", "US")
    assert type(industrial_strategy).__name__ == "CalculateDCFUseCase"
