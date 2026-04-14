import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.asyncio
async def test_read_root(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Welcome to Intrinsic Valuation API"}

@pytest.mark.asyncio
async def test_get_stocks_mocked(async_client: AsyncClient):
    with patch('app.api.routes.fetch_stock_metrics') as mock_fetch:
        mock_fetch.return_value = {
            "ticker": "MOCK3.SA", 
            "price": 10.0,
            "p_fcf": 2.0, "pe": 4.0, "eps": 2.5, "debt_ebit": 1.0,
            "roic": 10.0, "roe": 15.0, "net_margin": 12.0, "peg": 0.5, 
            "dividend_yield": 8.0, "p_vpa": 1.2
        }
        response = await async_client.get("/api/stocks/br?tickers=MOCK3", timeout=10.0)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "MOCK3.SA"
        assert data[0]["price"] == 10.0
