from pydantic import BaseModel, Field
from typing import Optional, List

class WACC(BaseModel):
    cost_of_equity: float = Field(..., description="Cost of Equity (Ke)")
    cost_of_debt: float = Field(..., description="Cost of Debt (Kd)")
    weight_of_equity: float = Field(..., description="Weight of Equity in Capital Structure")
    weight_of_debt: float = Field(..., description="Weight of Debt in Capital Structure")
    tax_rate: float = Field(..., description="Effective Tax Rate")
    value: float = Field(..., description="Calculated WACC")

class FinancialStatement(BaseModel):
    ticker: str
    year: int
    revenue: float = 0.0
    ebit: float = 0.0
    net_income: float = 0.0
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    working_capital: float = 0.0
    retained_earnings: float = 0.0
    operating_cash_flow: float = 0.0
    capital_expenditure: float = 0.0
    free_cash_flow: float = 0.0
    shares_outstanding: int = 1
    
class Stock(BaseModel):
    ticker: str
    exchange: str = "US" # US or B3
    sector: str = "Industrial" # e.g., Industrial, Financial, REIT, FII
    current_price: float = 0.0
    beta: float = 1.0
    market_cap: float = 0.0
    historical_statements: List[FinancialStatement] = []

class ScenarioResult(BaseModel):
    scenario_name: str # Base, Bull, Bear
    intrinsic_value: float
    margin_of_safety: float

class ValuationResult(BaseModel):
    ticker: str
    strategy_used: str
    current_price: float
    z_score: Optional[float] = None
    roic_3yr_avg: Optional[float] = None
    is_distressed: bool = False
    scenarios: List[ScenarioResult]
    probability_density: Optional[dict] = None # For Monte Carlo outputs
