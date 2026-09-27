from ..core.entities import FinancialStatement

class CalculateZScoreUseCase:
    @staticmethod
    def execute(statement: FinancialStatement, market_cap: float) -> float:
        """
        Calculates the Altman Z-Score.
        Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5
        """
        if statement.total_assets == 0:
            return 0.0
            
        x1 = statement.working_capital / statement.total_assets
        x2 = statement.retained_earnings / statement.total_assets
        x3 = statement.ebit / statement.total_assets
        
        total_liabilities = statement.total_liabilities
        x4 = market_cap / total_liabilities if total_liabilities > 0 else 0
        
        x5 = statement.revenue / statement.total_assets
        
        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
        return z_score

class ROICCalculator:
    @staticmethod
    def execute(statement: FinancialStatement) -> float:
        """
        Simplified ROIC = EBIT * (1 - tax) / Invested Capital
        Invested Capital = Total Assets - Current Liabilities - Cash (simplified to Total Assets - Working Capital for now)
        """
        invested_capital = statement.total_assets - (statement.total_assets - statement.total_liabilities - statement.working_capital)
        if invested_capital <= 0:
            return 0.0
            
        tax_rate = 0.21 # Defaulting to standard corporate tax rate for simplicity
        nopat = statement.ebit * (1 - tax_rate)
        return nopat / invested_capital
