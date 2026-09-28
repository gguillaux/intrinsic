from sqlalchemy import create_engine, Column, String, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta, timezone
import os

Base = declarative_base()

class CacheEntry(Base):
    __tablename__ = 'financial_cache'
    
    ticker = Column(String, primary_key=True)
    provider = Column(String, primary_key=True)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data = Column(JSON)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "intrinsic_cache.sqlite")

_engine = None
_SessionLocal = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
        Base.metadata.create_all(_engine)
    return _engine

def _get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine())
    return _SessionLocal

def get_cached_fundamentals(ticker: str, provider: str, max_age_hours: int = 24) -> dict:
    SessionLocal = _get_session()
    with SessionLocal() as session:
        entry = session.query(CacheEntry).filter_by(ticker=ticker, provider=provider).first()
        if entry:
            if datetime.now(timezone.utc) - entry.last_updated.replace(tzinfo=timezone.utc) < timedelta(hours=max_age_hours):
                return entry.data
    return None

def set_cached_fundamentals(ticker: str, provider: str, data: dict):
    SessionLocal = _get_session()
    with SessionLocal() as session:
        entry = session.query(CacheEntry).filter_by(ticker=ticker, provider=provider).first()
        if entry:
            entry.data = data
            entry.last_updated = datetime.now(timezone.utc)
        else:
            new_entry = CacheEntry(ticker=ticker, provider=provider, data=data)
            session.add(new_entry)
        session.commit()
