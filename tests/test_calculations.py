"""Tests for domain calculation functions — pure logic, no mocks needed."""
import pytest
from app.domain.calculations import (
    compute_ceiling_price,
    compute_sharpe_ratio,
    compute_total_return_12m,
    calculate_ranking,
    enrich_fii_metrics,
    apply_magic_formula,
    FII_MIN_DAILY_LIQUIDITY,
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


class TestTotalReturn:
    def test_basic_total_return(self):
        # 12m price appreciation 5.5% + dividend yield 8.5% = 14.0%
        assert compute_total_return_12m(val_12m=5.5, dividend_yield=8.5) == 14.0

    def test_negative_price_return(self):
        # Price dropped -10%, but DY was 8% -> net -2%
        assert compute_total_return_12m(val_12m=-10.0, dividend_yield=8.0) == -2.0

    def test_none_val_returns_none(self):
        assert compute_total_return_12m(val_12m=None, dividend_yield=8.0) is None

    def test_none_dy_treated_as_zero(self):
        assert compute_total_return_12m(val_12m=5.0, dividend_yield=None) == 5.0


class TestSharpeRatio:
    def test_basic_positive_sharpe(self):
        result = compute_sharpe_ratio(min_52w=80.0, max_52w=120.0, annual_return=20.0, selic_rate=10.0)
        assert result is not None
        assert result > 0  # 20% return vs 10% risk-free → positive

    def test_negative_sharpe(self):
        result = compute_sharpe_ratio(min_52w=80.0, max_52w=120.0, annual_return=5.0, selic_rate=10.0)
        assert result is not None
        assert result < 0  # 5% return vs 10% risk-free → negative

    def test_val_cagr_backward_compatibility(self):
        result = compute_sharpe_ratio(min_52w=80.0, max_52w=120.0, val_cagr=20.0, selic_rate=10.0)
        assert result is not None
        assert result > 0

    def test_none_min_returns_none(self):
        assert compute_sharpe_ratio(min_52w=None, max_52w=120.0, annual_return=20.0, selic_rate=10.0) is None

    def test_zero_min_returns_none(self):
        assert compute_sharpe_ratio(min_52w=0.0, max_52w=120.0, annual_return=20.0, selic_rate=10.0) is None

    def test_none_annual_return_returns_none(self):
        assert compute_sharpe_ratio(min_52w=80.0, max_52w=120.0, annual_return=None, selic_rate=10.0) is None


class TestRanking:
    def _make_stocks(self):
        return [
            {"ticker": "A", "peg": 0.5, "p_fcf": 10, "pe": 8, "eps": 5, "debt_ebit": 2, "roic": 20, "roe": 25, "net_margin": 15, "dividend_yield": 6},
            {"ticker": "B", "peg": 0.8, "p_fcf": 15, "pe": 12, "eps": 3, "debt_ebit": 4, "roic": 15, "roe": 18, "net_margin": 10, "dividend_yield": 4},
            {"ticker": "C", "peg": 0.3, "p_fcf": 8,  "pe": 6,  "eps": 7, "debt_ebit": 1, "roic": 25, "roe": 30, "net_margin": 20, "dividend_yield": 8},
        ]

    def test_stock_ranking_assigns_all_fields(self):
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

    def test_fii_ranking_prioritizes_ffo_and_pvp(self):
        fiis = [
            {"ticker": "FII_EXPENSIVE", "ffo_yield": 5.0, "p_vpa": 1.3, "sharpe_ratio": 0.1, "dy_cagr": 2.0, "dividend_yield": 6.0},
            {"ticker": "FII_VALUE",     "ffo_yield": 11.0, "p_vpa": 0.85, "sharpe_ratio": 0.8, "dy_cagr": 8.0, "dividend_yield": 10.0},
        ]
        result = calculate_ranking(fiis, 'reit')
        ranked = {item['ticker']: item['final_rank'] for item in result}
        assert ranked["FII_VALUE"] == 1
        assert ranked["FII_EXPENSIVE"] == 2

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
            {
                "ticker": "FII1", "price": 100.0, "dividend_yield": 8.0,
                "val_12m": 5.0, "min_52w": 80.0, "max_52w": 120.0,
                "p_vpa": 0.9, "ffo_yield": 7.5, "dy_cagr": 5.0, "liquidez": 2_000_000.0
            },
            {
                "ticker": "FII2", "price": 50.0, "dividend_yield": 10.0,
                "val_12m": -2.0, "min_52w": 40.0, "max_52w": 60.0,
                "p_vpa": 1.1, "ffo_yield": 9.0, "dy_cagr": 8.0, "liquidez": 1_500_000.0
            },
        ]
        result = enrich_fii_metrics(data, ntnb_rate=6.0, spread=4.0, selic_rate=10.5)
        for item in result:
            assert 'ceiling_price' in item
            assert 'total_return_12m' in item
            assert 'sharpe_ratio' in item
            assert 'final_rank' in item
            assert item['ceiling_price'] is not None
            assert item['total_return_12m'] is not None
            assert item['sharpe_ratio'] is not None
            assert item['final_rank'] is not None

    def test_illiquid_fii_is_excluded_from_ranking(self):
        data = [
            {
                "ticker": "LIQUID", "price": 100.0, "dividend_yield": 9.0,
                "val_12m": 6.0, "min_52w": 90.0, "max_52w": 110.0,
                "p_vpa": 0.95, "ffo_yield": 8.5, "dy_cagr": 6.0, "liquidez": 1_000_000.0
            },
            {
                "ticker": "ILLIQUID", "price": 80.0, "dividend_yield": 12.0,
                "val_12m": 20.0, "min_52w": 70.0, "max_52w": 90.0,
                "p_vpa": 0.80, "ffo_yield": 11.0, "dy_cagr": 10.0, "liquidez": 50_000.0 # < 500k threshold
            },
        ]
        result = enrich_fii_metrics(data, ntnb_rate=6.0, spread=4.0, selic_rate=10.5)
        by_ticker = {item['ticker']: item for item in result}
        assert by_ticker["LIQUID"]["final_rank"] == 1
        assert by_ticker["ILLIQUID"]["final_rank"] is None
        assert by_ticker["ILLIQUID"]["rank_score"] is None


class TestApplyMagicFormula:
    def test_basic_magic_formula_ranking(self):
        # 4 tickers:
        # A: ebit_ev = 12.0, roc_gb = 40.0 -> rank_ey = 1, rank_roc = 2 -> score = 3
        # B: ebit_ev = 8.0,  roc_gb = 50.0 -> rank_ey = 3, rank_roc = 1 -> score = 4
        # C: ebit_ev = 10.0, roc_gb = 30.0 -> rank_ey = 2, rank_roc = 3 -> score = 5
        # D: ebit_ev = 5.0,  roc_gb = 20.0 -> rank_ey = 4, rank_roc = 4 -> score = 8
        stocks = [
            {"ticker": "D", "ebit_ev": 5.0, "roc_gb": 20.0},
            {"ticker": "A", "ebit_ev": 12.0, "roc_gb": 40.0},
            {"ticker": "C", "ebit_ev": 10.0, "roc_gb": 30.0},
            {"ticker": "B", "ebit_ev": 8.0, "roc_gb": 50.0},
        ]
        res = apply_magic_formula(stocks)
        by_ticker = {item["ticker"]: item for item in res}

        assert by_ticker["A"]["magic_rank_ey"] == 1
        assert by_ticker["A"]["magic_rank_roc"] == 2
        assert by_ticker["A"]["magic_score"] == 3
        assert by_ticker["A"]["magic_rank"] == 1

        assert by_ticker["B"]["magic_rank_ey"] == 3
        assert by_ticker["B"]["magic_rank_roc"] == 1
        assert by_ticker["B"]["magic_score"] == 4
        assert by_ticker["B"]["magic_rank"] == 2

        assert by_ticker["C"]["magic_rank_ey"] == 2
        assert by_ticker["C"]["magic_rank_roc"] == 3
        assert by_ticker["C"]["magic_score"] == 5
        assert by_ticker["C"]["magic_rank"] == 3

        assert by_ticker["D"]["magic_rank_ey"] == 4
        assert by_ticker["D"]["magic_rank_roc"] == 4
        assert by_ticker["D"]["magic_score"] == 8
        assert by_ticker["D"]["magic_rank"] == 4

    def test_ineligible_financials_and_negative_values(self):
        stocks = [
            {"ticker": "NORMAL", "ebit_ev": 10.0, "roc_gb": 25.0},
            {"ticker": "BANK", "ebit_ev": 12.0, "roc_gb": None},       # Financials: missing ROC
            {"ticker": "LOSS", "ebit_ev": -2.0, "roc_gb": -5.0},       # Loss-maker: negative values
            {"ticker": "NO_EV", "ebit_ev": None, "roc_gb": 30.0},      # Missing EV
        ]
        res = apply_magic_formula(stocks)
        by_ticker = {item["ticker"]: item for item in res}

        assert by_ticker["NORMAL"]["magic_rank"] == 1
        assert by_ticker["BANK"]["magic_rank"] is None
        assert by_ticker["BANK"]["magic_score"] is None
        assert by_ticker["LOSS"]["magic_rank"] is None
        assert by_ticker["NO_EV"]["magic_rank"] is None

    def test_tie_breaking_by_earnings_yield(self):
        # Tie in magic_score (score = 3):
        # T1: EY rank 1 (15%), ROC rank 2 (20%) -> score 3
        # T2: EY rank 2 (10%), ROC rank 1 (30%) -> score 3
        # Tie-breaker prioritizes higher ebit_ev (T1 should get rank 1, T2 rank 2)
        stocks = [
            {"ticker": "T2", "ebit_ev": 10.0, "roc_gb": 30.0},
            {"ticker": "T1", "ebit_ev": 15.0, "roc_gb": 20.0},
        ]
        res = apply_magic_formula(stocks)
        by_ticker = {item["ticker"]: item for item in res}
        assert by_ticker["T1"]["magic_score"] == 3
        assert by_ticker["T2"]["magic_score"] == 3
        assert by_ticker["T1"]["magic_rank"] == 1
        assert by_ticker["T2"]["magic_rank"] == 2

