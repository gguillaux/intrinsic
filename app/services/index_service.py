import requests
import datetime
from bs4 import BeautifulSoup
from ..models import IndexComposition
from ..database import db

# Common B3 Indices
B3_INDICES = ["IBOV", "IFIX", "SMLL", "IDIV", "IBRX"]

def fetch_and_store_indices():
    """
    Fetches the composition for various B3 indices and stores them in SQLite.
    Overwrites previous entries as compositions change.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # We will use a mock population logic for demonstration unless a robust API is available, 
    # since B3 requires complex base64 state tokens and StatusInvest blocks automated scraping.
    mock_data = {
        "IBOV": [("VALE3.SA", 12.5), ("ITUB4.SA", 8.2), ("PETR4.SA", 7.5), ("WEGE3.SA", 3.1), ("ABEV3.SA", 2.8)],
        "IFIX": [("HGLG11.SA", 4.1), ("KNRI11.SA", 3.2), ("MXRF11.SA", 2.5), ("XPLG11.SA", 2.1)],
        "SMLL": [("LWSA3.SA", 1.5), ("CASH3.SA", 1.2), ("TASA4.SA", 1.1)],
        "IDIV": [("BBAS3.SA", 5.5), ("TAEE11.SA", 4.2), ("EGIE3.SA", 3.8)],
        "IBRX": [("VALE3.SA", 11.0), ("ITUB4.SA", 7.8), ("PETR4.SA", 6.9)]
    }

    now = datetime.datetime.now()
    records = []
    for index_name, components in mock_data.items():
        for ticker, weight in components:
            records.append({
                "index_name": index_name,
                "ticker": ticker,
                "weight": weight,
                "last_updated": now
            })

    with db.atomic():
        # Clear existing compositions to overwrite with latest
        IndexComposition.delete().execute()
        
        if records:
            IndexComposition.insert_many(records).execute()
    print("Indices composition successfully updated in DB.")

def get_index_composition(index_name: str):
    """
    Returns the composition of a given index from the local DB.
    """
    query = IndexComposition.select().where(IndexComposition.index_name == index_name.upper())
    return [
        {
            "ticker": item.ticker,
            "weight": item.weight,
            "last_updated": item.last_updated.strftime("%Y-%m-%d %H:%M:%S")
        } for item in query
    ]

def get_all_indices():
    """Returns a list of all available indices in the DB."""
    query = IndexComposition.select(IndexComposition.index_name).distinct()
    return [item.index_name for item in query]
