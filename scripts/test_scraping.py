import yfinance as yf
from bs4 import BeautifulSoup
import requests
import urllib.parse

def test_fetch(ticker, category):
    url = f'https://statusinvest.com.br/{category}/{ticker.lower()}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    res = requests.get(url, headers=headers)
    print(f"{category} status: {res.status_code}")
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        name_tag = soup.find('h1')
        print(f"H1 tag: {name_tag.text.strip() if name_tag else 'None'}")
        
test_fetch("vcra11", "fundos-imobiliarios")
test_fetch("vcra11", "fiagros")
test_fetch("cdii11", "fiinfras")
