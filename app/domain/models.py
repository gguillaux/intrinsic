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
    # FII-specific (Fundamentus)
    segmento: Optional[str] = None
    vp_cota: Optional[float] = None
    ffo_yield: Optional[float] = None
    ffo_cota: Optional[float] = None
    ffo_payout: Optional[float] = None      # Rend. distribuído / FFO (12m), %
    liquidez: Optional[float] = None        # Average daily traded volume (R$, 2 months)
    cap_rate: Optional[float] = None
    vacancia: Optional[float] = None
    caixa: Optional[float] = None           # Cash as % of total assets
    dy_cagr: Optional[float] = None         # Dividend-per-share CAGR 3y, %
    # Earnings Yield & Magic Formula (Greenblatt)
    earnings_yield: Optional[float] = None   # EPS / price, %
    ebit_ev: Optional[float] = None          # EBIT / Enterprise Value, %
    roc_gb: Optional[float] = None           # EBIT / (NWC + Net PPE), % (Greenblatt ROC)
    magic_rank_ey: Optional[int] = None      # Cross-sectional rank on EBIT/EV (1 = best)
    magic_rank_roc: Optional[int] = None     # Cross-sectional rank on ROC (1 = best)
    magic_score: Optional[int] = None        # magic_rank_ey + magic_rank_roc
    magic_rank: Optional[int] = None         # Final Magic Formula rank (1 = best)
    magic_pct_ey: Optional[float] = None     # Percentile rank on EBIT/EV (0-100, 100 = best)
    magic_pct_roc: Optional[float] = None    # Percentile rank on ROC (0-100, 100 = best)
    magic_pct_score: Optional[float] = None  # Normalized composite average (magic_pct_ey + magic_pct_roc) / 2
    # Computed / ranking fields
    total_return_12m: Optional[float] = None
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
