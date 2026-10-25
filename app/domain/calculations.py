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


# --- Total Return ---

def compute_total_return_12m(
    val_12m: Optional[float],
    dividend_yield: Optional[float]
) -> Optional[float]:
    """
    12-month total return of a FII holder (%): price change + distributions yield.

    Returns None when the price change is unknown. A missing DY counts as 0.
    """
    if val_12m is None:
        return None
    return round(val_12m + (dividend_yield or 0.0), 2)


# --- Sharpe Ratio (Parkinson Volatility) ---

def compute_sharpe_ratio(
    min_52w: Optional[float],
    max_52w: Optional[float],
    annual_return: Optional[float] = None,
    selic_rate: float = 10.5,
    **kwargs: Any
) -> Optional[float]:
    """
    Computes the Sharpe Ratio using Parkinson's High-Low volatility estimator.

    Parkinson Volatility = (1 / (2 × sqrt(ln2))) × ln(High / Low)
    Sharpe = (Return - RiskFreeRate) / Volatility

    Args:
        min_52w: 52-week low price.
        max_52w: 52-week high price.
        annual_return: Annual return (as percentage, e.g. 12.5). For FIIs this is
            the 12-month total return (price change + dividend yield).
        selic_rate: Selic rate (as percentage, e.g. 10.5).

    Returns:
        The Sharpe Ratio, or None if inputs are insufficient.
    """
    if annual_return is None and "val_cagr" in kwargs:
        annual_return = kwargs["val_cagr"]

    if not min_52w or not max_52w or min_52w <= 0 or annual_return is None:
        return None

    ln_hl = math.log(max_52w / min_52w)
    parkinson_volatility = (1 / (2 * math.sqrt(math.log(2)))) * ln_hl

    if parkinson_volatility <= 0:
        return None

    return_decimal = annual_return / 100
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

# FII ranking: recurring cash generation (FFO Yield) leads, since DY can be
# inflated by asset sales or reserves. P/VP, risk-adjusted return and
# dividend growth follow; raw DY has the lowest weight.
FII_RANKING_INDICATORS = [
    {"key": "ffo_yield",      "filter": lambda v: v is not None and v > 0, "asc": False, "weight": 0.25},
    {"key": "p_vpa",          "filter": lambda v: v is not None and v > 0, "asc": True,  "weight": 0.20},
    {"key": "sharpe_ratio",   "filter": lambda v: v is not None,           "asc": False, "weight": 0.20},
    {"key": "dy_cagr",        "filter": lambda v: v is not None,           "asc": False, "weight": 0.20},
    {"key": "dividend_yield", "filter": lambda v: v is not None and v > 0, "asc": False, "weight": 0.15},
]

# FIIs trading less than this (R$/day, 2-month average) are shown but not ranked.
FII_MIN_DAILY_LIQUIDITY = 500_000


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
    selic_rate: float = 10.5,
    min_liquidity: float = FII_MIN_DAILY_LIQUIDITY,
) -> List[Dict[str, Any]]:
    """
    Enriches FII metric dicts with computed fields (ceiling_price,
    total_return_12m, sharpe_ratio) and then applies ranking.

    FIIs with known daily liquidity below `min_liquidity` are kept in the
    output but excluded from the ranking (final_rank/rank_score = None).

    Args:
        data: List of FII metric dictionaries.
        ntnb_rate: NTN-B coupon rate (%).
        spread: Premium spread (%).
        selic_rate: Selic rate (%).
        min_liquidity: Minimum average daily traded volume (R$) to be ranked.

    Returns:
        The enriched and ranked list.
    """
    for item in data:
        item['ceiling_price'] = compute_ceiling_price(
            item.get('price'), item.get('dividend_yield'), ntnb_rate, spread
        )
        item['total_return_12m'] = compute_total_return_12m(
            item.get('val_12m'), item.get('dividend_yield')
        )
        item['sharpe_ratio'] = compute_sharpe_ratio(
            item.get('min_52w'), item.get('max_52w'), item['total_return_12m'], selic_rate
        )

    def is_liquid(item: Dict[str, Any]) -> bool:
        liquidity = item.get('liquidez')
        return liquidity is None or liquidity >= min_liquidity

    rankable = [item for item in data if is_liquid(item)]
    calculate_ranking(rankable, 'reit')
    for item in data:
        if not is_liquid(item):
            item['rank_score'] = None
            item['final_rank'] = None
    return data


def apply_magic_formula(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Computes cross-sectional Joel Greenblatt Magic Formula ranking for a list of stocks.

    Eligible stocks must have positive EBIT/EV (ebit_ev > 0) and positive
    Greenblatt ROC (roc_gb > 0).

    Ranking method:
      1. rank_ey: position sorted by ebit_ev descending (1 = highest earnings yield)
      2. rank_roc: position sorted by roc_gb descending (1 = highest return on capital)
      3. magic_score: rank_ey + rank_roc (lower is better)
      4. magic_rank: 1..N sorted by magic_score ascending (ties broken by ebit_ev descending)

    Ineligible stocks (e.g. financials/banks without NWC, missing EBIT, negative EV/EBIT)
    receive None for all magic_* fields.
    """
    for item in data:
        item['magic_rank_ey'] = None
        item['magic_rank_roc'] = None
        item['magic_score'] = None
        item['magic_rank'] = None

    eligible = [
        item for item in data
        if item.get('ebit_ev') is not None and item.get('ebit_ev') > 0
        and item.get('roc_gb') is not None and item.get('roc_gb') > 0
    ]

    if not eligible:
        return data

    # 1. Rank on EBIT / EV (Earnings Yield) descending
    sorted_by_ey = sorted(eligible, key=lambda x: x['ebit_ev'], reverse=True)
    curr_rank = 1
    for i, item in enumerate(sorted_by_ey):
        if i > 0 and item['ebit_ev'] < sorted_by_ey[i - 1]['ebit_ev']:
            curr_rank = i + 1
        item['magic_rank_ey'] = curr_rank

    # 2. Rank on ROC (Return on Capital) descending
    sorted_by_roc = sorted(eligible, key=lambda x: x['roc_gb'], reverse=True)
    curr_rank = 1
    for i, item in enumerate(sorted_by_roc):
        if i > 0 and item['roc_gb'] < sorted_by_roc[i - 1]['roc_gb']:
            curr_rank = i + 1
        item['magic_rank_roc'] = curr_rank

    # 3. Combined score
    for item in eligible:
        item['magic_score'] = item['magic_rank_ey'] + item['magic_rank_roc']

    # 4. Final Magic Rank: lower score is better; ties broken by higher ebit_ev, then roc_gb
    sorted_final = sorted(
        eligible,
        key=lambda x: (x['magic_score'], -(x['ebit_ev'] or 0), -(x['roc_gb'] or 0))
    )
    curr_rank = 1
    for i, item in enumerate(sorted_final):
        if i > 0 and (
            item['magic_score'], item['ebit_ev'], item['roc_gb']
        ) != (
            sorted_final[i - 1]['magic_score'],
            sorted_final[i - 1]['ebit_ev'],
            sorted_final[i - 1]['roc_gb'],
        ):
            curr_rank = i + 1
        item['magic_rank'] = curr_rank

    return data

