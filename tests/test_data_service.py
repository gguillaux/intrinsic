import pytest
from app.services.data_service import _compute_ttm_fcf, _init_empty_metrics, _populate_yfinance_fundamentals
import pandas as pd
from unittest.mock import MagicMock

def test_compute_ttm_fcf_quarterly():
    # Arrange
    data = _init_empty_metrics("MOCK3.SA")
    data["price"] = 20.0
    tc_mock = MagicMock()
    tc_mock.info = {'sharesOutstanding': 1000}
    
    # Mocking quarterly cashflow Series
    qcf_data = {
        'Free Cash Flow': [1000.0, 2000.0, 3000.0, 4000.0, 5000.0]
    }
    qcf_df = pd.DataFrame(qcf_data).T
    tc_mock.quarterly_cashflow = qcf_df
    
    # Act
    _compute_ttm_fcf('MOCK3.SA', data, tc_mock)
    
    # Assert
    # TTM = 1000 + 2000 + 3000 + 4000 = 10000
    # Shares = 1000 -> FCF_PS = 10.0 -> P/FCF = 20.0 / 10.0 = 2.0
    assert data["p_fcf"] == 2.0

def test_compute_ttm_fcf_annual_fallback():
    # Arrange
    data = _init_empty_metrics("MOCK3.SA")
    data["price"] = 50.0
    tc_mock = MagicMock()
    tc_mock.info = {'sharesOutstanding': 500}
    
    # Empty quarterly
    tc_mock.quarterly_cashflow = pd.DataFrame()
    
    # Annual cashflow
    acf_data = {
        'Free Cash Flow': [2500.0, 1000.0]
    }
    tc_mock.cashflow = pd.DataFrame(acf_data).T
    
    # Act
    _compute_ttm_fcf('MOCK3.SA', data, tc_mock)
    
    # Assert
    # Annual TTM = 2500 -> Shares = 500 -> FCF_PS = 5 -> P/FCF = 50 / 5 = 10.0
    assert data["p_fcf"] == 10.0


class TestPopulateYfinanceFundamentals:
    """Tests for _populate_yfinance_fundamentals conversion and null handling."""

    def test_converts_percentages_correctly(self):
        data = _init_empty_metrics("TEST")
        info = {
            'trailingEps': 5.0,
            'trailingPE': 20.0,
            'pegRatio': 1.5,
            'returnOnEquity': 0.25,    # 25%
            'returnOnAssets': 0.10,    # 10%
            'profitMargins': 0.15,     # 15%
            'dividendYield': 0.34,     # 0.34% (yfinance format)
        }
        _populate_yfinance_fundamentals(data, info)
        assert data['eps'] == 5.0
        assert data['pe'] == 20.0
        assert data['peg'] == 1.5
        assert data['roe'] == 25.0     # ×100
        assert data['roic'] == 10.0    # ×100
        assert data['net_margin'] == 15.0  # ×100
        assert data['dividend_yield'] == 0.34  # NOT ×100

    def test_computes_debt_ebit(self):
        data = _init_empty_metrics("TEST")
        info = {
            'totalDebt': 500_000,
            'totalCash': 100_000,
            'ebitda': 200_000,
        }
        _populate_yfinance_fundamentals(data, info)
        # Net debt = 500k - 100k = 400k, debt/ebitda = 400k / 200k = 2.0
        assert data['debt_ebit'] == 2.0

    def test_debt_ebit_without_cash(self):
        data = _init_empty_metrics("TEST")
        info = {
            'totalDebt': 300_000,
            'ebitda': 100_000,
            # no totalCash key
        }
        _populate_yfinance_fundamentals(data, info)
        assert data['debt_ebit'] == 3.0

    def test_skips_debt_ebit_when_ebitda_zero(self):
        data = _init_empty_metrics("TEST")
        info = {'totalDebt': 500_000, 'ebitda': 0}
        _populate_yfinance_fundamentals(data, info)
        assert data['debt_ebit'] is None

    def test_handles_all_none_values(self):
        data = _init_empty_metrics("TEST")
        info = {}
        _populate_yfinance_fundamentals(data, info)
        # All fields should remain None
        for key in ['eps', 'pe', 'peg', 'roe', 'roic', 'net_margin', 'dividend_yield', 'p_vpa', 'debt_ebit']:
            assert data[key] is None

    def test_handles_partial_data(self):
        data = _init_empty_metrics("TEST")
        info = {'trailingEps': 3.5}  # only EPS provided
        _populate_yfinance_fundamentals(data, info)
        assert data['eps'] == 3.5
        assert data['pe'] is None
        assert data['roe'] is None

    def test_price_to_book(self):
        data = _init_empty_metrics("TEST")
        info = {'priceToBook': 2.3456}
        _populate_yfinance_fundamentals(data, info)
        assert data['p_vpa'] == 2.3456  # rounded to 4 decimals

