import logging
import time
from datetime import datetime
from sqlmodel import Session, select
from app.models import Asset
from app.sources.status_invest import StatusInvestSource
from app.database import engine

logger = logging.getLogger(__name__)

DEFAULT_TICKERS = [
    "PRIO3", "RANI3", "UNIP6", "ITSA4", "PSSA3", "CXSE3", "SIMH3",
    "RECV3", "PETR4", "WIZC3", "BBSE3", "BBAS3", "TTEN3", "FIQE3", "BRBI11",
    "SOJA3", "CPFE3", "VALE3", "KEPL3", "EGIE3", "B3SA3", "VAMO3"
]

class AssetService:
    def __init__(self):
        self.source = StatusInvestSource()

    def sync_assets(self, tickers: list[str] = None):
        tickers = tickers or DEFAULT_TICKERS
        logger.info(f"Syncing {len(tickers)} assets from Status Invest...")
        
        with Session(engine) as session:
            for ticker in tickers:
                data = self.source.get_asset_data(ticker)
                if data:
                    statement = select(Asset).where(Asset.ticker == ticker.upper())
                    existing = session.exec(statement).first()
                    
                    if existing:
                        for key, value in data.model_dump(exclude={"ticker"}).items():
                            setattr(existing, key, value)
                        existing.updated_at = datetime.utcnow()
                    else:
                        session.add(data)
                    
                    session.commit()
                    logger.info(f"Updated {ticker}")
                
                # Avoid rate limiting
                time.sleep(1)

    def get_assets(self):
        with Session(engine) as session:
            statement = select(Asset).order_by(Asset.ticker)
            return session.exec(statement).all()
