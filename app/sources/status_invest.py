import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from app.models import Asset
from app.utils import HEADERS, clean_value

logger = logging.getLogger(__name__)

class StatusInvestSource:
    base_url = "https://statusinvest.com.br/acoes"

    def __init__(self):
        self.session = requests.Session()

    def get_asset_data(self, ticker: str) -> Optional[Asset]:
        url = f"{self.base_url}/{ticker.lower()}"
        try:
            response = self.session.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, "lxml")
            
            return Asset(
                ticker=ticker.upper(),
                price=self._find_by_label(soup, "cotação") or 0.0,
                pe=self._find_by_label(soup, "p/l"),
                dy=self._find_by_label(soup, "dividend yield"),
                p_vp=self._find_by_label(soup, "p/vp"),
                roe=self._find_by_label(soup, "roe"),
                roic=self._find_by_label(soup, "roic"),
                ev_ebit=self._find_by_label(soup, "ev/ebit")
            )
        except Exception as e:
            logger.error(f"Error fetching StatusInvest data for {ticker}: {e}")
            return None

    def _find_by_label(self, soup: BeautifulSoup, label: str) -> Optional[float]:
        elements = soup.find_all(["span", "div", "td", "h3"], string=lambda t: t and label.lower() in t.lower())
        for elem in elements:
            # Common pattern in Status Invest: value is in a sibling or parent sibling
            parent = elem.parent
            if parent:
                val_elem = parent.find(class_="value") or parent.find_next_sibling()
                if val_elem:
                    return clean_value(val_elem.get_text(strip=True))
        return None
