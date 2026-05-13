"""
Domain Calculations — Pure financial formulas.

All functions in this module are pure: they take inputs and return outputs
with no side effects, no API calls, no database access. This makes them
trivially testable and completely framework-independent.
"""
import math
from typing import List, Dict, Any, Optional


# --- Ceiling Price (Preço Teto) ---

def compute_ceiling_price(
    price: Optional[float],
    dividend_yield: Optional[float],
    ntnb_rate: float,
    spread: float
) -> Optional[float]:
    """
    Computes the ceiling price for a FII based on the Gordon Growth Model variant.

    Formula: ceiling = (price × dividend_yield) / (ntnb_rate + spread)

    Args:
        price: Current market price.
        dividend_yield: Current dividend yield (as percentage, e.g. 8.5).
        ntnb_rate: NTN-B 10Y coupon rate (as percentage, e.g. 6.0).
        spread: Premium spread over NTN-B (as percentage, e.g. 4.0).

    Returns:
        The ceiling price, or None if inputs are insufficient.
    """
    required_yield = ntnb_rate + spread
    if required_yield == 0 or price is None or dividend_yield is None:
        return None
    return (price * dividend_yield) / required_yield


# --- Sharpe Ratio (Parkinson Volatility) ---

def compute_sharpe_ratio(
    min_52w: Optional[float],
    max_52w: Optional[float],
    val_cagr: Optional[float],
    selic_rate: float
) -> Optional[float]:
    """
    Computes the Sharpe Ratio using Parkinson's High-Low volatility estimator.

    Parkinson Volatility = (1 / (2 × sqrt(ln2))) × ln(High / Low)
    Sharpe = (Return - RiskFreeRate) / Volatility

    Args:
        min_52w: 52-week low price.
        max_52w: 52-week high price.
        val_cagr: Valorization CAGR 3y (as percentage, e.g. 12.5).
        selic_rate: Selic rate (as percentage, e.g. 10.5).

    Returns:
        The Sharpe Ratio, or None if inputs are insufficient.
    """
    if not min_52w or not max_52w or min_52w <= 0 or val_cagr is None:
        return None

    ln_hl = math.log(max_52w / min_52w)
    parkinson_volatility = (1 / (2 * math.sqrt(math.log(2)))) * ln_hl

    if parkinson_volatility <= 0:
        return None

    return_decimal = val_cagr / 100
    selic_decimal = selic_rate / 100

    return (return_decimal - selic_decimal) / parkinson_volatility


# --- Ranking Algorithm ---

# Default ranking weights for stocks (all equal)
STOCK_RANKING_INDICATORS = [
    {"key": "peg",            "filter": lambda v: v is not None and v > 0 and v <= 1, "asc": True,  "weight": 1.0},
    {"key": "p_fcf",          "filter": lambda v: v is not None and v > 0,            "asc": True,  "weight": 1.0},
    {"key": "pe",             "filter": lambda v: v is not None and v > 0,            "asc": True,  "weight": 1.0},
    {"key": "eps",            "filter": lambda v: v is not None and v > 0,            "asc": False, "weight": 1.0},
    {"key": "debt_ebit",      "filter": lambda v: v is not None and v > 0,            "asc": True,  "weight": 1.0},
    {"key": "roic",           "filter": lambda v: v is not None and v > 0,            "asc": False, "weight": 1.0},
    {"key": "roe",            "filter": lambda v: v is not None and v > 0,            "asc": False, "weight": 1.0},
    {"key": "net_margin",     "filter": lambda v: v is not None and v > 0,            "asc": False, "weight": 1.0},
    {"key": "dividend_yield", "filter": lambda v: v is not None and v > 0,            "asc": False, "weight": 1.0},
]

# FII ranking: DY CAGR and Sharpe heavily weighted
FII_RANKING_INDICATORS = [
    {"key": "dy_cagr",        "filter": lambda v: v is not None, "asc": False, "weight": 0.35},
    {"key": "sharpe_ratio",   "filter": lambda v: v is not None, "asc": False, "weight": 0.35},
    {"key": "dividend_yield", "filter": lambda v: v is not None, "asc": False, "weight": 0.15},
    {"key": "p_vpa",          "filter": lambda v: v is not None, "asc": True,  "weight": 0.15},
]


def calculate_ranking(data: List[Dict[str, Any]], asset_type: str) -> List[Dict[str, Any]]:
    """
    Applies a multi-indicator ranking algorithm to a list of asset metrics.

    Each indicator sorts the assets and assigns position-based scores multiplied
    by the indicator's weight. Lower total score = better rank.

    Args:
        data: List of metric dictionaries.
        asset_type: Either 'stock' or 'reit'.

    Returns:
        The same list with 'rank_score' and 'final_rank' fields populated.
    """
    if asset_type not in ('stock', 'reit'):
        return data

    indicators = STOCK_RANKING_INDICATORS if asset_type == 'stock' else FII_RANKING_INDICATORS

    # Initialize scores
    for item in data:
        item['rank_score'] = 0.0

    for indicator in indicators:
        key = indicator['key']
        valid_items = []
        invalid_items = []

        for item in data:
            value = item.get(key)
            if value is not None and indicator['filter'](value):
                valid_items.append(item)
            else:
                invalid_items.append(item)

        # Sort valid items by indicator value
        valid_items.sort(key=lambda x: x.get(key, 0), reverse=not indicator['asc'])

        # Assign position-based scores
        for position, item in enumerate(valid_items):
            item['rank_score'] += (position + 1) * indicator['weight']

        # Penalize invalid items
        penalty = (len(valid_items) + 1) * indicator['weight']
        for item in invalid_items:
            item['rank_score'] += penalty

    # Assign final ranks
    sorted_by_score = sorted(data, key=lambda x: x['rank_score'])
    for position, item in enumerate(sorted_by_score):
        item['final_rank'] = position + 1
        item['rank_score'] = round(item['rank_score'], 2)

    return data


def enrich_fii_metrics(
    data: List[Dict[str, Any]],
    ntnb_rate: float = 6.0,
    spread: float = 4.0,
    selic_rate: float = 10.5
) -> List[Dict[str, Any]]:
    """
    Enriches FII metric dicts with computed fields (ceiling_price, sharpe_ratio)
    and then applies ranking.

    Args:
        data: List of FII metric dictionaries.
        ntnb_rate: NTN-B coupon rate (%).
        spread: Premium spread (%).
        selic_rate: Selic rate (%).

    Returns:
        The enriched and ranked list.
    """
    for item in data:
        item['ceiling_price'] = compute_ceiling_price(
            item.get('price'), item.get('dividend_yield'), ntnb_rate, spread
        )
        item['sharpe_ratio'] = compute_sharpe_ratio(
            item.get('min_52w'), item.get('max_52w'), item.get('val_cagr'), selic_rate
        )

    return calculate_ranking(data, 'reit')
