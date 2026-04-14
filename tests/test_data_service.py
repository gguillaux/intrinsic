import pytest
from app.services.data_service import _compute_ttm_fcf, _init_empty_metrics
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
