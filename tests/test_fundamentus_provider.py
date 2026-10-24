"""
Unit tests for FundamentusProvider using offline HTML fixtures.
"""
import os
import pytest
from app.providers.fundamentus_provider import (
    parse_br_number,
    parse_listing,
    parse_details,
    details_to_metrics,
    FundamentusProvider,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read_fixture(filename: str) -> str:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "r", encoding="latin-1") as f:
        return f.read()


class TestParseBrNumber:
    def test_decimal_comma(self):
        assert parse_br_number("156,42") == pytest.approx(156.42)

    def test_percentage_string(self):
        assert parse_br_number("8,51%") == pytest.approx(8.51)

    def test_thousands_separator(self):
        assert parse_br_number("7.133.020.000") == 7133020000.0

    def test_negative_number(self):
        assert parse_br_number("-1.548.970") == -1548970.0

    def test_empty_or_dash(self):
        assert parse_br_number("") is None
        assert parse_br_number("-") is None
        assert parse_br_number("--") is None
        assert parse_br_number(None) is None


class TestParseListing:
    @pytest.fixture(scope="class")
    def listing_html(self):
        return _read_fixture("fundamentus_fii_resultado.html")

    def test_extracts_hglg11(self, listing_html):
        result = parse_listing(listing_html)
        assert "HGLG11" in result
        hglg = result["HGLG11"]
        assert hglg["segmento"] == "Multicategoria"
        assert hglg["p_vpa"] is not None
        assert hglg["p_vpa"] > 0
        assert hglg["ffo_yield"] is not None
        assert hglg["dividend_yield"] is not None
        assert hglg["liquidez"] is not None
        assert hglg["cap_rate"] is not None
        assert hglg["vacancia"] is not None

    def test_paper_fii_resets_zero_cap_rate_and_vacancy(self, listing_html):
        result = parse_listing(listing_html)
        assert "MXRF11" in result
        mxrf = result["MXRF11"]
        # MXRF11 has 0% cap rate in raw table -> treated as None (not applicable)
        assert mxrf["cap_rate"] is None
        assert mxrf["vacancia"] is None


class TestParseDetails:
    @pytest.fixture(scope="class")
    def hglg_details_html(self):
        return _read_fixture("fundamentus_detalhes_hglg11.html")

    @pytest.fixture(scope="class")
    def mxrf_details_html(self):
        return _read_fixture("fundamentus_detalhes_mxrf11.html")

    def test_hglg_details_metrics(self, hglg_details_html):
        raw = parse_details(hglg_details_html)
        metrics = details_to_metrics(raw)
        assert metrics.get("vp_cota") is not None
        assert metrics["vp_cota"] > 100.0  # ~165
        assert metrics.get("min_52w") is not None
        assert metrics.get("max_52w") is not None
        assert metrics["min_52w"] > 100.0
        assert metrics.get("ffo_payout") is not None
        # Distributed rendimentos / FFO
        assert 90.0 < metrics["ffo_payout"] < 130.0

    def test_mxrf_details_metrics(self, mxrf_details_html):
        raw = parse_details(mxrf_details_html)
        metrics = details_to_metrics(raw)
        assert metrics.get("vp_cota") is not None
        assert 5.0 < metrics["vp_cota"] < 15.0  # MXRF11 is base ~10
        assert metrics.get("min_52w") is not None
        assert metrics.get("max_52w") is not None


class TestFundamentusProviderIntegration:
    def test_fetch_reit_merges_metrics(self, monkeypatch):
        listing_html = _read_fixture("fundamentus_fii_resultado.html")
        details_html = _read_fixture("fundamentus_detalhes_hglg11.html")

        provider = FundamentusProvider()
        monkeypatch.setattr(provider, "_get_listing", lambda: parse_listing(listing_html))
        monkeypatch.setattr(provider, "_get_details", lambda t: details_to_metrics(parse_details(details_html)))

        data = {"ticker": "HGLG11.SA", "price": 156.0}
        provider.fetch_reit("HGLG11.SA", data)

        assert data["p_vpa"] is not None
        assert data["vp_cota"] is not None
        assert data["ffo_yield"] is not None
        assert data["dividend_yield"] is not None
        assert data["segmento"] is not None
        assert data["liquidez"] is not None
        assert data["min_52w"] is not None
        assert data["max_52w"] is not None
        # Price should stay from yfinance if provided
        assert data["price"] == 156.0
