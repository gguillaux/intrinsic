import re
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from app.models import News

logger = logging.getLogger(__name__)

class B3NewsSource:
    BASE_URL = "https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias"
    
    def __init__(self):
        self.session = requests.Session()

    def fetch_news(self, days: int = 3) -> List[News]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "agencia": 18,
            "palavra": "",
            "dataInicial": start_date.strftime("%Y-%m-%d"),
            "dataFinal": end_date.strftime("%Y-%m-%d")
        }
        
        try:
            response = self.session.get(f"{self.BASE_URL}/ListarTitulosNoticias", params=params)
            response.raise_for_status()
            data = response.json()
            
            news_list = []
            for item in data:
                msg = item.get("NwsMsg", {})
                headline = msg.get("headline", "")
                external_id = msg.get("id")
                date_str = msg.get("dateTime")
                
                if not headline or not external_id:
                    continue
                    
                ticker = self._extract_ticker(headline)
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                
                news_list.append(News(
                    external_id=external_id,
                    date_time=dt,
                    ticker=ticker,
                    headline=headline
                ))
            return news_list
        except Exception as e:
            logger.error(f"Error fetching B3 news: {e}")
            return []

    def _extract_ticker(self, headline: str) -> Optional[str]:
        # Regex to find Ticker inside parentheses, e.g., (PETR4)
        match = re.search(r'\((\w{4}[3456]|ALPA4|BPAC11|SULA11|UNIP6)\)', headline)
        if match:
            return match.group(1)
        # Fallback for general 4 letters + number pattern
        match = re.search(r'\(([A-Z]{4}[0-9]{1,2})\)', headline)
        return match.group(1) if match else None

    def get_detail(self, news_id: int, date_str: str) -> str:
        params = {
            "idNoticia": news_id,
            "agencia": 18,
            "dataNoticia": date_str
        }
        try:
            response = self.session.get(f"{self.BASE_URL}/Detail", params=params)
            return response.text
        except Exception as e:
            logger.error(f"Error fetching news detail {news_id}: {e}")
            return "Could not retrieve details."
