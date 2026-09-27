"""
Domain models for financial metrics.
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class StockMetrics:
    ticker: str
    name: str = ""
    price: Optional[float] = None
    market_cap: Optional[float] = None
    p_s: Optional[float] = None
    p_fcf: Optional[float] = None
    pe: Optional[float] = None
    p_a: Optional[float] = None
    p_nwc: Optional[float] = None
    eps: Optional[float] = None
    debt_ebit: Optional[float] = None
    roic: Optional[float] = None
    roe: Optional[float] = None
    net_margin: Optional[float] = None
    peg: Optional[float] = None
    dividend_yield: Optional[float] = None
    p_vpa: Optional[float] = None
    min_52w: Optional[float] = None
    max_52w: Optional[float] = None
    val_12m: Optional[float] = None
    vp_cota: Optional[float] = None
    caixa: Optional[float] = None
    dy_cagr: Optional[float] = None
    val_cagr: Optional[float] = None
    cotistas: Optional[int] = None
    # Computed / ranking fields
    rank_score: Optional[float] = None
    final_rank: Optional[int] = None
    ceiling_price: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to standard metrics dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockMetrics":
        """Instantiate StockMetrics from dictionary, ignoring unexpected keys."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
