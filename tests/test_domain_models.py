"""
Tests for domain StockMetrics model.
"""
from app.domain.models import StockMetrics


def test_stock_metrics_defaults():
    m = StockMetrics(ticker="PETR4.SA", name="Petrobras")
    assert m.ticker == "PETR4.SA"
    assert m.name == "Petrobras"
    assert m.price is None
    d = m.to_dict()
    assert isinstance(d, dict)
    assert d["ticker"] == "PETR4.SA"
    assert "price" in d


def test_stock_metrics_from_dict():
    raw = {
        "ticker": "AAPL",
        "name": "Apple",
        "price": 180.5,
        "pe": 28.5,
        "unexpected_extra_key": "ignore_me",
    }
    m = StockMetrics.from_dict(raw)
    assert m.ticker == "AAPL"
    assert m.price == 180.5
    assert m.pe == 28.5
    assert not hasattr(m, "unexpected_extra_key")
