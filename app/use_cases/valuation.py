import numpy as np
from ..core.entities import Stock, ScenarioResult, ValuationResult
from ..core.interfaces import IValuationStrategy

def _generate_monte_carlo_distribution(mean: float, std_dev: float, iterations: int = 10000) -> np.ndarray:
    return np.random.normal(mean, std_dev, iterations)

class CalculateDCFUseCase(IValuationStrategy):
    def __init__(self, iterations: int = 10000):
        self.iterations = iterations

    def calculate_intrinsic_value(self, stock: Stock, **kwargs) -> ValuationResult:
        if not stock.historical_statements:
            raise ValueError(f"No historical financial statements available for {stock.ticker}")

        # In a real scenario, these would be derived from historical variance
        base_growth_rate = kwargs.get('growth_rate', 0.05)
        growth_std_dev = kwargs.get('growth_std_dev', 0.02)
        
        terminal_growth_rate = kwargs.get('terminal_growth_rate', 0.02)
        discount_rate = kwargs.get('discount_rate', 0.10)
        
        latest_statement = stock.historical_statements[-1]
        latest_fcf = latest_statement.free_cash_flow
        
        # Monte Carlo Simulation
        growth_distribution = _generate_monte_carlo_distribution(base_growth_rate, growth_std_dev, self.iterations)
        
        simulated_values = []
        for g in growth_distribution:
            # Simple 5 year projection
            projected_fcfs = [latest_fcf * ((1 + g) ** i) for i in range(1, 6)]
            terminal_value = (projected_fcfs[-1] * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
            
            discounted_fcfs = sum([fcf / ((1 + discount_rate) ** i) for i, fcf in enumerate(projected_fcfs, 1)])
            discounted_tv = terminal_value / ((1 + discount_rate) ** 5)
            
            intrinsic_equity_value = discounted_fcfs + discounted_tv
            per_share_value = intrinsic_equity_value / latest_statement.shares_outstanding if latest_statement.shares_outstanding > 0 else 0
            simulated_values.append(per_share_value)
            
        simulated_values = np.array(simulated_values)
        
        # Calculate Scenarios
        base_value = float(np.median(simulated_values))
        bear_value = float(np.percentile(simulated_values, 20))
        bull_value = float(np.percentile(simulated_values, 80))
        
        def margin_of_safety(iv: float) -> float:
            if stock.current_price <= 0: return 0.0
            return (iv - stock.current_price) / stock.current_price
            
        scenarios = [
            ScenarioResult(scenario_name="Bear Case", intrinsic_value=bear_value, margin_of_safety=margin_of_safety(bear_value)),
            ScenarioResult(scenario_name="Base Case", intrinsic_value=base_value, margin_of_safety=margin_of_safety(base_value)),
            ScenarioResult(scenario_name="Bull Case", intrinsic_value=bull_value, margin_of_safety=margin_of_safety(bull_value)),
        ]
        
        return ValuationResult(
            ticker=stock.ticker,
            strategy_used="DCF with Monte Carlo",
            current_price=stock.current_price,
            scenarios=scenarios,
            probability_density={
                "mean": float(np.mean(simulated_values)),
                "std_dev": float(np.std(simulated_values)),
                "p5": float(np.percentile(simulated_values, 5)),
                "p95": float(np.percentile(simulated_values, 95))
            }
        )

class CalculateDDMUseCase(IValuationStrategy):
    def calculate_intrinsic_value(self, stock: Stock, **kwargs) -> ValuationResult:
        # Simplified DDM for FIIs / REITs
        dividend_yield = kwargs.get('expected_dividend', 1.0)
        discount_rate = kwargs.get('discount_rate', 0.10)
        growth_rate = kwargs.get('growth_rate', 0.02)
        
        if discount_rate <= growth_rate:
            intrinsic_value = 0.0
        else:
            intrinsic_value = dividend_yield / (discount_rate - growth_rate)
            
        margin = (intrinsic_value - stock.current_price) / stock.current_price if stock.current_price > 0 else 0
        
        scenarios = [
            ScenarioResult(scenario_name="Base Case", intrinsic_value=intrinsic_value, margin_of_safety=margin)
        ]
        
        return ValuationResult(
            ticker=stock.ticker,
            strategy_used="Dividend Discount Model",
            current_price=stock.current_price,
            scenarios=scenarios
        )
