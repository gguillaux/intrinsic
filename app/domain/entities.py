"""
Domain Entities — The single source of truth for data shapes.

These dataclasses define the canonical business objects used across the entire
application. Every other layer (API schemas, database serialization, frontend
rendering) derives its shape from these definitions.

No framework imports allowed here — only stdlib.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ValuationMetric:
    """Represents the fundamental valuation metrics for a single financial asset."""

    ticker: str
    name: str = ""
    price: Optional[float] = None

    # Valuation Ratios
    p_fcf: Optional[float] = None
    pe: Optional[float] = None
    p_a: Optional[float] = None
    eps: Optional[float] = None
    debt_ebit: Optional[float] = None
    peg: Optional[float] = None

    # Profitability
    roic: Optional[float] = None
    roe: Optional[float] = None
    net_margin: Optional[float] = None

    # Yield & Book
    dividend_yield: Optional[float] = None
    p_vpa: Optional[float] = None

    # Price Action
    min_52w: Optional[float] = None
    max_52w: Optional[float] = None
    val_12m: Optional[float] = None

    # FII/REIT Specific
    vp_cota: Optional[float] = None
    caixa: Optional[float] = None
    dy_cagr: Optional[float] = None
    val_cagr: Optional[float] = None
    cotistas: Optional[int] = None

    # Computed Fields (populated by domain calculations)
    ceiling_price: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    def is_valid(self) -> bool:
        """A metric is considered valid if it has a price."""
        return self.price is not None

    def to_dict(self) -> dict:
        """Converts to a plain dictionary for serialization."""
        return asdict(self)

    @classmethod
    def empty(cls, ticker: str) -> "ValuationMetric":
        """Factory method to create an empty metric with only the ticker set."""
        return cls(ticker=ticker, name=ticker)

    @classmethod
    def from_dict(cls, data: dict) -> "ValuationMetric":
        """Creates a ValuationMetric from a dictionary, ignoring unknown keys."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)
