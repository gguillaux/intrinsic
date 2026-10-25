"""
Tests for Strategy pattern provider infrastructure.
"""
from app.providers.base import MetricsProvider
from app.providers.yfinance_provider import YFinanceProvider, resolve_price
from app.services.data_service import get_providers, register_provider, _init_empty_metrics


def test_provider_registration_and_ordering():
    providers = get_providers()
    assert len(providers) >= 1
    priorities = [p.priority for p in providers]
    assert priorities == sorted(priorities)
    names = [p.name for p in providers]
    assert "yfinance" in names


def test_custom_provider_can_be_registered():
    class DummyProvider(MetricsProvider):
        @property
        def name(self) -> str:
            return "dummy"

        @property
        def priority(self) -> int:
            return 5  # runs before yfinance

        def fetch_stock(self, ticker, data, **kwargs):
            data["name"] = f"Dummy {ticker}"

        def fetch_reit(self, ticker, data, **kwargs):
            pass

    dummy = DummyProvider()
    register_provider(dummy)
    providers = get_providers()
    assert providers[0].name == "dummy"

    data = _init_empty_metrics("TEST")
    dummy.fetch_stock("TEST", data)
    assert data["name"] == "Dummy TEST"


def test_resolve_price_helper():
    class MockFastInfo:
        last_price = 42.5

    assert resolve_price({}, MockFastInfo()) == 42.5
    assert resolve_price({"currentPrice": 99.0}, None) == 99.0
    assert resolve_price({"regularMarketPrice": 88.0}, None) == 88.0
    assert resolve_price({}, None) is None


def test_earnings_yield_calculation():
    from app.providers.yfinance_provider import populate_fundamentals
    
    # Positive EPS & Price
    data = {"price": 50.0}
    populate_fundamentals(data, {"trailingEps": 5.0})
    assert data["eps"] == 5.0
    assert data["earnings_yield"] == 10.0  # (5.0 / 50.0) * 100

    # Negative EPS (loss-maker)
    data = {"price": 20.0}
    populate_fundamentals(data, {"trailingEps": -2.0})
    assert data["eps"] == -2.0
    assert data["earnings_yield"] == -10.0

    # Missing price
    data = {"price": None}
    populate_fundamentals(data, {"trailingEps": 3.0})
    assert data["eps"] == 3.0
    assert "earnings_yield" not in data


def test_compute_magic_formula_inputs():
    import pandas as pd
    from app.providers.yfinance_provider import compute_magic_formula_inputs

    # Standard case with quarterly EBIT
    qf = pd.DataFrame(
        {"2024-Q4": [250.0], "2024-Q3": [250.0], "2024-Q2": [250.0], "2024-Q1": [250.0]},
        index=["EBIT"]
    )
    fin = pd.DataFrame({"2024": [900.0]}, index=["EBIT"])
    bs = pd.DataFrame(
        {"2024": [2000.0, 3000.0]},
        index=["Working Capital", "Net PPE"]
    )
    info = {
        "enterpriseValue": 10000.0,
        "currency": "BRL",
        "financialCurrency": "BRL",
    }
    # TTM EBIT = 1000.0
    # EV = 10000.0 -> ebit_ev = 10.0%
    # NWC = 2000, PPE = 3000 -> Capital = 5000 -> roc_gb = 1000 / 5000 = 20.0%
    res = compute_magic_formula_inputs(info, fin, qf, bs)
    assert res["ebit_ev"] == 10.0
    assert res["roc_gb"] == 20.0


def test_compute_magic_formula_inputs_fallbacks_and_guards():
    import pandas as pd
    from app.providers.yfinance_provider import compute_magic_formula_inputs

    # Fallback to annual Operating Income and balance sheet line items
    qf = pd.DataFrame() # empty quarterly
    fin = pd.DataFrame({"2024": [500.0]}, index=["Operating Income"])
    bs = pd.DataFrame(
        {"2024": [1500.0, 500.0, 4000.0, 1000.0]},
        index=["Current Assets", "Current Liabilities", "Gross PPE", "Accumulated Depreciation"]
    )
    # NWC = 1500 - 500 = 1000
    # Net PPE = 4000 - 1000 = 3000
    # Invested Capital = 4000 -> ROC = 500 / 4000 = 12.5%
    # EV computed from marketCap + totalDebt - totalCash
    info = {
        "marketCap": 4000.0,
        "totalDebt": 1500.0,
        "totalCash": 500.0, # EV = 5000 -> ebit_ev = 500 / 5000 = 10.0%
        "currency": "USD",
        "financialCurrency": "USD",
    }
    res = compute_magic_formula_inputs(info, fin, qf, bs)
    assert res["ebit_ev"] == 10.0
    assert res["roc_gb"] == 12.5

    # Currency mismatch guard (e.g. ADRs in ARS/USD)
    info_mismatch = dict(info)
    info_mismatch["financialCurrency"] = "ARS"
    res_mismatch = compute_magic_formula_inputs(info_mismatch, fin, qf, bs)
    assert res_mismatch["ebit_ev"] is None  # guarded!
    assert res_mismatch["roc_gb"] == 12.5   # dimensionless capital ratio still preserved

    # Bank/financials guard (no working capital / current assets)
    bs_bank = pd.DataFrame({"2024": [3000.0]}, index=["Net PPE"])
    res_bank = compute_magic_formula_inputs(info, fin, qf, bs_bank)
    assert res_bank["roc_gb"] is None  # Bank has no working capital

