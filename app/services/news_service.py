import logging
import requests
import datetime
import json
from ..models import News
from typing import Optional

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15  # seconds

def fetch_and_store_news(target_date_str: Optional[str] = None):
    """
    Fetches the news from B3 for a specific date and stores them.
    If no date is provided, defaults to today.
    target_date_str format: 'YYYY-MM-DD'
    """
    try:
        if target_date_str:
            target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
        else:
            target_date = datetime.date.today()
    except ValueError:
        target_date = datetime.date.today()
        
    start_date = target_date - datetime.timedelta(days=3) # small window around the date
    endDateStr = target_date.strftime('%Y-%m-%d')
    startDateStr = start_date.strftime('%Y-%m-%d')
    
    url = f"https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/ListarTitulosNoticias?agencia=18&palavra=&dataInicial={startDateStr}&dataFinal={endDateStr}"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            new_count = 0
            for item in data:
                msg = item.get("NwsMsg", {})
                if "id" in msg and "headline" in msg:
                    id_noticia = msg["id"]
                    title = msg["headline"]
                    dt = msg.get("dateTime", "")
                    date_param = dt[:10] if dt else endDateStr
                    full_link = f"https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Detail?idNoticia={id_noticia}&agencia=18&dataNoticia={date_param}"
                    
                    if not News.select().where(News.link == full_link).exists():
                        try:
                            pub_dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S") if dt else datetime.datetime.now()
                        except ValueError:
                            pub_dt = datetime.datetime.now()
                            
                        News.create(
                            title=title,
                            link=full_link,
                            published_at=pub_dt,
                            source="B3"
                        )
                        new_count += 1
            logger.info("Stored %d new news items for %s", new_count, endDateStr)
    except Exception as e:
        logger.error("Failed to fetch news: %s", e)

    # Return fetched news from DB around the requested date
    # In SQLite DateTimeField strings are formatted nicely, we can use simple string matching
    like_str = f"{endDateStr}%"
    return list(News.select().where(News.published_at ** like_str).order_by(News.published_at.desc()).limit(50).dicts())
