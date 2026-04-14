from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import requests_cache
from datetime import timedelta
from .api import routes
from .database import init_db
from .services.index_service import fetch_and_store_indices
from .services.news_service import fetch_and_store_news

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQL database tables
    init_db()
    # Fetch latest data for indices and news
    fetch_and_store_indices()
    fetch_and_store_news()
    yield

app = FastAPI(title="Intrinsic Valuation API", version="2.0.0", lifespan=lifespan)

# Setup global requests cache (SQLite backend, 6h expiration)
requests_cache.install_cache(
    'intrinsic_cache', 
    backend='sqlite', 
    expire_after=timedelta(hours=6)
)



# Allow CORS for local frontend testing
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
