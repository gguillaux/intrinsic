import requests
import datetime
import json
from ..models import News

def fetch_and_store_news(target_date_str: str = None):
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
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            
            new_count = 0
            for a in links:
                href = a.get('href')
                if href and 'Detail' in href:
                    title = a.text.strip()
                    full_link = f"https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/{href}"
                    
                    if not News.select().where(News.link == full_link).exists():
                        News.create(
                            title=title,
                            link=full_link,
                            published_at=datetime.datetime.now(),
                            source="B3"
                        )
                        new_count += 1
            print(f"Stored {new_count} new news items for {endDateStr}.")
    except Exception as e:
        print("Error fetching news:", e)

    # Return fetched news from DB around the requested date
    # In SQLite DateTimeField strings are formatted nicely, we can use simple string matching
    like_str = f"{endDateStr}%"
    return list(News.select().where(News.published_at ** like_str).order_by(News.published_at.desc()).limit(50).dicts())
