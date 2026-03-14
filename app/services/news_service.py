import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select, delete
from app.models import News
from app.sources.b3_news import B3NewsSource
from app.database import engine

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        self.source = B3NewsSource()

    def sync_news(self):
        logger.info("Syncing B3 news...")
        news_items = self.source.fetch_news(days=3)
        
        with Session(engine) as session:
            new_count = 0
            for item in news_items:
                # Check if exists
                statement = select(News).where(News.external_id == item.external_id)
                existing = session.exec(statement).first()
                
                if not existing:
                    session.add(item)
                    new_count += 1
            
            session.commit()
            logger.info(f"Sync complete. Added {new_count} new items.")
            
            # Clean old news (> 30 days)
            self._cleanup_old_news(session)

    def _cleanup_old_news(self, session: Session):
        limit_date = datetime.now() - timedelta(days=30)
        statement = delete(News).where(News.date_time < limit_date)
        session.exec(statement)
        session.commit()
        logger.info("Old news cleanup complete.")

    def get_latest_news(self, ticker: str = None, limit: int = 50):
        with Session(engine) as session:
            statement = select(News).order_by(News.date_time.desc()).limit(limit)
            if ticker:
                statement = statement.where(News.ticker == ticker.upper())
            return session.exec(statement).all()
