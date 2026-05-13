"""Tests for domain calculation functions — pure logic, no mocks needed."""
import pytest
from app.domain.calculations import (
    compute_ceiling_price,
    compute_sharpe_ratio,
    calculate_ranking,
    enrich_fii_metrics,
)


class TestCeilingPrice:
    def test_basic_calculation(self):
        result = compute_ceiling_price(price=100.0, dividend_yield=8.0, ntnb_rate=6.0, spread=4.0)
        assert result == pytest.approx(80.0)  # (100 * 8) / (6 + 4) = 80

    def test_high_yield_above_ceiling(self):
        result = compute_ceiling_price(price=50.0, dividend_yield=12.0, ntnb_rate=5.0, spread=3.0)
        assert result == pytest.approx(75.0)  # (50 * 12) / 8 = 75 → price < ceiling

    def test_none_price_returns_none(self):
        assert compute_ceiling_price(price=None, dividend_yield=8.0, ntnb_rate=6.0, spread=4.0) is None

    def test_none_dy_returns_none(self):
        assert compute_ceiling_price(price=100.0, dividend_yield=None, ntnb_rate=6.0, spread=4.0) is None

    def test_zero_denominator_returns_none(self):
        assert compute_ceiling_price(price=100.0, dividend_yield=8.0, ntnb_rate=0.0, spread=0.0) is None


class TestSharpeRatio:
    def test_basic_positive_sharpe(self):
        result = compute_sharpe_ratio(min_52w=80.0, max_52w=120.0, val_cagr=20.0, selic_rate=10.0)
        assert result is not None
        assert result > 0  # 20% return vs 10% risk-free → positive

    def test_negative_sharpe(self):
        result = compute_sharpe_ratio(min_52w=80.0, max_52w=120.0, val_cagr=5.0, selic_rate=10.0)
        assert result is not None
        assert result < 0  # 5% return vs 10% risk-free → negative

    def test_none_min_returns_none(self):
        assert compute_sharpe_ratio(min_52w=None, max_52w=120.0, val_cagr=20.0, selic_rate=10.0) is None

    def test_zero_min_returns_none(self):
        assert compute_sharpe_ratio(min_52w=0.0, max_52w=120.0, val_cagr=20.0, selic_rate=10.0) is None

    def test_none_val_cagr_returns_none(self):
        assert compute_sharpe_ratio(min_52w=80.0, max_52w=120.0, val_cagr=None, selic_rate=10.0) is None


class TestRanking:
    def _make_stocks(self):
        return [
            {"ticker": "A", "peg": 0.5, "p_fcf": 10, "pe": 8, "eps": 5, "debt_ebit": 2, "roic": 20, "roe": 25, "net_margin": 15, "dividend_yield": 6},
            {"ticker": "B", "peg": 0.8, "p_fcf": 15, "pe": 12, "eps": 3, "debt_ebit": 4, "roic": 15, "roe": 18, "net_margin": 10, "dividend_yield": 4},
            {"ticker": "C", "peg": 0.3, "p_fcf": 8,  "pe": 6,  "eps": 7, "debt_ebit": 1, "roic": 25, "roe": 30, "net_margin": 20, "dividend_yield": 8},
        ]

    def test_ranking_assigns_all_fields(self):
        data = self._make_stocks()
        result = calculate_ranking(data, 'stock')
        for item in result:
            assert 'rank_score' in item
            assert 'final_rank' in item

    def test_best_stock_gets_rank_1(self):
        data = self._make_stocks()
        result = calculate_ranking(data, 'stock')
        ranked = {item['ticker']: item['final_rank'] for item in result}
        # Stock C has best values across all indicators
        assert ranked['C'] == 1

    def test_ranking_handles_null_values(self):
        data = [
            {"ticker": "X", "peg": None, "p_fcf": None, "pe": None, "eps": None, "debt_ebit": None, "roic": None, "roe": None, "net_margin": None, "dividend_yield": None},
            {"ticker": "Y", "peg": 0.5, "p_fcf": 10, "pe": 8, "eps": 5, "debt_ebit": 2, "roic": 20, "roe": 25, "net_margin": 15, "dividend_yield": 6},
        ]
        result = calculate_ranking(data, 'stock')
        ranked = {item['ticker']: item['final_rank'] for item in result}
        assert ranked['Y'] == 1  # X gets penalized for all nulls
        assert ranked['X'] == 2

    def test_unknown_type_returns_unchanged(self):
        data = [{"ticker": "A"}]
        result = calculate_ranking(data, 'unknown')
        assert result == data


class TestEnrichFiiMetrics:
    def test_enrichment_adds_computed_fields(self):
        data = [
            {"ticker": "FII1", "price": 100, "dividend_yield": 8, "min_52w": 80, "max_52w": 120, "val_cagr": 15, "p_vpa": 0.9, "dy_cagr": 5},
            {"ticker": "FII2", "price": 50,  "dividend_yield": 10, "min_52w": 40, "max_52w": 60, "val_cagr": 20, "p_vpa": 1.1, "dy_cagr": 8},
        ]
        result = enrich_fii_metrics(data, ntnb_rate=6.0, spread=4.0, selic_rate=10.5)
        for item in result:
            assert 'ceiling_price' in item
            assert 'sharpe_ratio' in item
            assert 'final_rank' in item
            assert item['ceiling_price'] is not None
            assert item['sharpe_ratio'] is not None
