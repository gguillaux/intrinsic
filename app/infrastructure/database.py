from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import os

Base = declarative_base()

class CacheEntry(Base):
    __tablename__ = 'financial_cache'
    
    ticker = Column(String, primary_key=True)
    provider = Column(String, primary_key=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "intrinsic_cache.sqlite")
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_cached_fundamentals(ticker: str, provider: str, max_age_hours: int = 24) -> dict:
    with SessionLocal() as session:
        entry = session.query(CacheEntry).filter_by(ticker=ticker, provider=provider).first()
        if entry:
            if datetime.utcnow() - entry.last_updated < timedelta(hours=max_age_hours):
                return entry.data
    return None

def set_cached_fundamentals(ticker: str, provider: str, data: dict):
    with SessionLocal() as session:
        entry = session.query(CacheEntry).filter_by(ticker=ticker, provider=provider).first()
        if entry:
            entry.data = data
            entry.last_updated = datetime.utcnow()
        else:
            new_entry = CacheEntry(ticker=ticker, provider=provider, data=data)
            session.add(new_entry)
        session.commit()
