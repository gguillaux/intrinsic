"""
Application Configuration — All constants and default values.

Centralizes magic numbers, default tickers, and configuration values
that were previously scattered across routes, services, and frontend.
"""

# --- External API Settings ---
REQUEST_TIMEOUT = 15  # seconds for all external HTTP requests

STATUS_INVEST_HEADERS = {
    'Accept': '*/*',
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Content-Type': 'application/x-www-form-urlencoded'
}

# StatusInvest API key → internal field name mapping
STATUSINVEST_INDICATOR_MAPPING = {
    'lpa': 'eps',
    'p_l': 'pe',
    'peg_Ratio': 'peg',
    'dy': 'dividend_yield',
    'p_vp': 'p_vpa',
    'dividaliquida_ebit': 'debt_ebit',
    'roic': 'roic',
    'roe': 'roe',
    'margemliquida': 'net_margin',
}

# --- Anomaly Detection ---
ANOMALY_THRESHOLD = 1000  # ROE/ROIC values above this are considered data glitches

# --- Cache Defaults ---
DEFAULT_CACHE_HOURS = 24

# --- Default Ticker Lists (fallback when user doesn't specify) ---
DEFAULT_BR_STOCKS = ["ABEV3.SA", "ITUB4.SA", "WEGE3.SA", "VALE3.SA"]
DEFAULT_US_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA"]
DEFAULT_BR_FIIS = ["HGLG11.SA", "MXRF11.SA", "KNRI11.SA", "XPLG11.SA"]
DEFAULT_US_REITS = ["O", "SPG", "PLD", "VNQ"]

# --- B3 Index Names ---
B3_INDICES = ["IBOV", "IFIX", "SMLL", "IDIV", "IBRX"]

# --- Macroeconomic Defaults ---
DEFAULT_NTNB_RATE = 6.0    # NTN-B 10Y coupon rate (%)
DEFAULT_SPREAD = 4.0       # Premium spread over NTN-B (%)
DEFAULT_SELIC_RATE = 10.5   # Selic rate (%)

# --- FII Scraping Categories ---
FII_CATEGORIES = ['fundos-imobiliarios', 'fiagros', 'fiinfras']
