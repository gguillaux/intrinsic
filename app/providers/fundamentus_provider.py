"""
Fundamentus data provider — Brazilian FII (REIT) fundamentals.

Fundamentus has no official API, so this provider scrapes two pages:

* ``fii_resultado.php`` — ONE request returns every listed FII with Segment,
  FFO Yield, Dividend Yield, P/VP, Market Cap, Liquidity, Cap Rate, Vacancy.
  Cached in memory (TTL) and shared across tickers.
* ``detalhes.php?papel=XXXX11`` — per ticker: VP/Cota, FFO/Cota, 52w range,
  12-month price change, FFO vs distributed income (payout) and asset
  composition (Caixa %).

Parsing is isolated in pure functions (``parse_br_number``, ``parse_listing``,
``parse_details``, ``details_to_metrics``) so it can be tested against saved
HTML fixtures. Network failures or layout changes never raise: fields simply
stay untouched (yfinance values remain as fallback).
"""
import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .base import MetricsProvider

logger = logging.getLogger(__name__)

BASE_URL = "https://www.fundamentus.com.br"
LISTING_URL = f"{BASE_URL}/fii_resultado.php"
DETAILS_URL = f"{BASE_URL}/detalhes.php"

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
HTTP_TIMEOUT = 15
LISTING_TTL_SECONDS = 3600
MIN_SECONDS_BETWEEN_REQUESTS = 0.3


# --- Pure parsing helpers ---

def parse_br_number(text: Optional[str]) -> Optional[float]:
    """Parses Brazilian formatted numbers: '1.234,56', '8,5%', '-1.548.970', 'R$ 3,20'."""
    if text is None:
        return None
    cleaned = str(text).strip().replace("R$", "").replace("%", "").replace("\xa0", "").strip()
    if cleaned in ("", "-", "--"):
        return None
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalize_label(text: str) -> str:
    return text.replace("?", "").strip()


def _decode(content: bytes) -> str:
    # Fundamentus serves ISO-8859-1 / cp1252 pages.
    try:
        return content.decode("cp1252")
    except UnicodeDecodeError:
        return content.decode("latin-1")


LISTING_COLUMNS = {
    "Segmento": "segmento",
    "Cotação": "price",
    "FFO Yield": "ffo_yield",
    "Dividend Yield": "dividend_yield",
    "P/VP": "p_vpa",
    "Valor de Mercado": "market_cap",
    "Liquidez": "liquidez",
    "Qtd de imóveis": "qtd_imoveis",
    "Cap Rate": "cap_rate",
    "Vacância Média": "vacancia",
}


def parse_listing(html: str) -> Dict[str, Dict[str, Any]]:
    """Parses fii_resultado.php into {TICKER: {field: value}}."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="tabelaResultado")
    if table is None:
        logger.warning("Fundamentus listing: table#tabelaResultado not found (layout changed?)")
        return {}

    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
    result: Dict[str, Dict[str, Any]] = {}

    for tr in table.find("tbody").find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        ticker = row.get("Papel", "").upper()
        if not ticker:
            continue

        entry: Dict[str, Any] = {}
        for column, field in LISTING_COLUMNS.items():
            if column not in row:
                continue
            entry[field] = row[column] if field == "segmento" else parse_br_number(row[column])

        # Paper FIIs (CRI) or funds without rental data report 0% cap rate/vacancy:
        # that's "not applicable", not "zero vacancy".
        if not entry.get("cap_rate"):
            entry["cap_rate"] = None
            entry["vacancia"] = None

        result[ticker] = entry
    return result


_COMPOSITION_RE = re.compile(r"name\s*:\s*'([^']*)'\s*,\s*data\s*:\s*\[\s*([\d.]+)\s*\]")


def parse_details(html: str) -> Dict[str, Any]:
    """
    Parses detalhes.php into a raw {label: text} dict plus a 'composition'
    dict ({asset class: BRL amount}) extracted from the chart script.

    Labels appearing twice (e.g. 'FFO' for last 12 months and last 3 months)
    keep the FIRST occurrence, which is the 12-month figure.
    """
    soup = BeautifulSoup(html, "lxml")
    raw: Dict[str, Any] = {}

    for label_td in soup.find_all("td", class_="label"):
        txt = label_td.find("span", class_="txt")
        label = _normalize_label(txt.get_text() if txt else label_td.get_text())
        data_td = label_td.find_next_sibling("td")
        if not label or data_td is None or "data" not in (data_td.get("class") or []):
            continue
        value_span = data_td.find("span", class_="txt")
        value = (value_span.get_text() if value_span else data_td.get_text()).strip()
        raw.setdefault(label, value)

    composition: Dict[str, float] = {}
    for name, amount in _COMPOSITION_RE.findall(html):
        try:
            composition[name.strip() or "Outros"] = composition.get(name.strip() or "Outros", 0.0) + float(amount)
        except ValueError:
            continue
    raw["composition"] = composition
    return raw


def details_to_metrics(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Maps raw detalhes.php labels into internal metric fields."""
    metrics: Dict[str, Any] = {
        "name": raw.get("Nome") or None,
        "segmento": raw.get("Segmento") or None,
        "min_52w": parse_br_number(raw.get("Min 52 sem")),
        "max_52w": parse_br_number(raw.get("Max 52 sem")),
        "liquidez": parse_br_number(raw.get("Vol $ méd (2m)")),
        "vp_cota": parse_br_number(raw.get("VP/Cota")),
        "ffo_cota": parse_br_number(raw.get("FFO/Cota")),
        "ffo_yield": parse_br_number(raw.get("FFO Yield")),
        "dividend_yield": parse_br_number(raw.get("Div. Yield")),
        "p_vpa": parse_br_number(raw.get("P/VP")),
        "val_12m": parse_br_number(raw.get("12 meses")),
    }

    ffo = parse_br_number(raw.get("FFO"))
    distributed = parse_br_number(raw.get("Rend. Distribuído"))
    if ffo and ffo > 0 and distributed is not None:
        metrics["ffo_payout"] = round(distributed / ffo * 100, 1)

    composition = raw.get("composition") or {}
    total = sum(composition.values())
    if total > 0:
        metrics["caixa"] = round(composition.get("Caixa", 0.0) / total * 100, 2)

    return {k: v for k, v in metrics.items() if v is not None}


# --- Provider ---

class FundamentusProvider(MetricsProvider):
    """Override provider for Brazilian FIIs (runs after yfinance)."""

    def __init__(self, session: Optional[requests.Session] = None):
        self._session = session or requests.Session()
        self._session.headers.update(HTTP_HEADERS)
        self._listing: Dict[str, Dict[str, Any]] = {}
        self._listing_fetched_at: float = 0.0
        self._lock = threading.Lock()
        self._last_request_at: float = 0.0

    @property
    def name(self) -> str:
        return "fundamentus"

    @property
    def priority(self) -> int:
        return 20

    # -- HTTP --

    def _get(self, url: str, params: Optional[Dict[str, str]] = None) -> Optional[str]:
        wait = MIN_SECONDS_BETWEEN_REQUESTS - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        try:
            response = self._session.get(url, params=params, timeout=HTTP_TIMEOUT)
            self._last_request_at = time.monotonic()
            response.raise_for_status()
            return _decode(response.content)
        except requests.RequestException as e:
            logger.warning("Fundamentus request failed (%s %s): %s", url, params, e)
            return None

    def _get_listing(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            if self._listing and time.monotonic() - self._listing_fetched_at < LISTING_TTL_SECONDS:
                return self._listing
            html = self._get(LISTING_URL)
            if html:
                parsed = parse_listing(html)
                if parsed:
                    self._listing = parsed
                    self._listing_fetched_at = time.monotonic()
            return self._listing

    def _get_details(self, ticker: str) -> Dict[str, Any]:
        html = self._get(DETAILS_URL, params={"papel": ticker})
        if not html:
            return {}
        raw = parse_details(html)
        if "FFO Yield" not in raw and "VP/Cota" not in raw:
            logger.warning("Fundamentus details for %s: unexpected layout or unknown ticker", ticker)
            return {}
        return details_to_metrics(raw)

    # -- Strategy interface --

    def fetch_stock(self, ticker: str, data: Dict[str, Any], **kwargs) -> None:
        """Stocks are out of scope for this provider."""
        return None

    def fetch_reit(self, ticker: str, data: Dict[str, Any], **kwargs) -> None:
        if not ticker.upper().endswith(".SA"):
            return
        papel = ticker.upper().replace(".SA", "")
        try:
            listing_entry = self._get_listing().get(papel, {})
            details = self._get_details(papel)

            merged: Dict[str, Any] = {}
            merged.update(details)
            # Listing has 2-decimal precision for yields (detail page rounds DY to 1 decimal).
            merged.update({k: v for k, v in listing_entry.items() if v is not None})

            # yfinance price is closer to real-time; only use Fundamentus close as fallback.
            fundamentus_price = merged.pop("price", None)
            if data.get("price") is None and fundamentus_price:
                data["price"] = fundamentus_price
            merged.pop("qtd_imoveis", None)

            # Keep a meaningful name if yfinance already provided one.
            if data.get("name") and data.get("name") != ticker:
                merged.pop("name", None)

            # Paper FIIs: cap rate/vacancy not applicable.
            if "cap_rate" in listing_entry and listing_entry.get("cap_rate") is None:
                merged["cap_rate"] = None
                merged["vacancia"] = None

            data.update(merged)
        except Exception as e:  # never break the endpoint
            logger.error("FundamentusProvider.fetch_reit failed for %s: %s", ticker, e)

    def get_listing_tickers(self) -> List[str]:
        """Utility: all FII tickers currently listed on Fundamentus."""
        return sorted(self._get_listing().keys())
