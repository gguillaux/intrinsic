import requests
import datetime
import json
from ..models import News

def fetch_and_store_news():
    """
    Fetches the latest news from B3 and stores new ones in SQLite.
    Returns the latest 50 news articles.
    """
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=7)
    
    url = f"https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/ListarTitulosNoticias?agencia=18&palavra=&dataInicial={start_date.strftime('%Y-%m-%d')}&dataFinal={today.strftime('%Y-%m-%d')}"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # The API returns HTML or JSON? Let's assume it returns HTML with a table or JSON list.
            # B3 endpoint actually returns HTML. We'll use a regex or bs4 to parse it.
            # For simplicity in this demo, let's mock the parsing if it's complex, or implement a basic one.
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            
            new_count = 0
            for a in links:
                href = a.get('href')
                if href and 'Detail' in href:
                    title = a.text.strip()
                    full_link = f"https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/{href}"
                    
                    # Store if not exists
                    if not News.select().where(News.link == full_link).exists():
                        News.create(
                            title=title,
                            link=full_link,
                            published_at=datetime.datetime.now(),
                            source="B3"
                        )
                        new_count += 1
            print(f"Stored {new_count} new news items.")
    except Exception as e:
        print("Error fetching news:", e)

    # Return latest from DB
    return list(News.select().order_by(News.published_at.desc()).limit(50).dicts())
