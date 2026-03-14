import logging
from fastapi import FastAPI
from dash import Dash
import dash_bootstrap_components as dbc
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import init_db
from app.services.news_service import NewsService
from app.services.asset_service import AssetService
from app.web.layout import create_layout
import app.web.callbacks # To register callbacks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DB
init_db()

# Services
news_service = NewsService()
asset_service = AssetService()

# FastAPI App
server = FastAPI()

@server.get("/api/health")
def health():
    return {"status": "ok"}

# Dash App
app = Dash(
    __name__, 
    server=server, 
    url_base_pathname="/",
    external_stylesheets=[dbc.themes.FLATLY]
)

app.layout = create_layout()

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(news_service.sync_news, 'interval', minutes=15, id='sync_news_job')
scheduler.add_job(asset_service.sync_assets, 'cron', hour=2, id='sync_assets_job') # Daily at 2AM
scheduler.start()

# Initial Sync (Async)
@server.on_event("startup")
def startup_event():
    # Trigger first syncs on startup if DB is empty
    news_service.sync_news()
    # asset_service.sync_assets() # Keep commented to avoid slow startup unless needed
