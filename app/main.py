import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .api import routes
from .database import init_db, db
from .services.index_service import fetch_and_store_indices
from .services.news_service import fetch_and_store_news

# Configure structured logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    init_db()
    fetch_and_store_indices()
    fetch_and_store_news()
    logger.info("Application startup complete.")
    yield
    # Shutdown
    logger.info("Closing database connection...")
    if not db.is_closed():
        db.close()
    logger.info("Application shutdown complete.")

app = FastAPI(title="Intrinsic Valuation API", version="3.0.0", lifespan=lifespan)

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to Intrinsic Valuation API"}
