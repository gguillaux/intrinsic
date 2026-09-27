"""
Tests for Strategy pattern provider infrastructure.
"""
from app.providers.base import MetricsProvider
from app.providers.yfinance_provider import YFinanceProvider, resolve_price
from app.providers.statusinvest_provider import StatusInvestProvider, parse_brazilian_currency
from app.services.data_service import get_providers, register_provider, _init_empty_metrics


def test_provider_registration_and_ordering():
    providers = get_providers()
    assert len(providers) >= 2
    priorities = [p.priority for p in providers]
    assert priorities == sorted(priorities)
    names = [p.name for p in providers]
    assert "yfinance" in names
    assert "statusinvest" in names


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


def test_parse_brazilian_currency():
    assert parse_brazilian_currency("R$ 1.234,56") == 1234.56
    assert parse_brazilian_currency("12,34%") == 12.34
    assert parse_brazilian_currency("-") is None
    assert parse_brazilian_currency("") is None
