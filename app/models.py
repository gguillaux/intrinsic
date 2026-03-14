from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class News(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    external_id: int = Field(index=True, unique=True)
    date_time: datetime = Field(index=True)
    ticker: Optional[str] = Field(default=None, index=True)
    headline: str
    source: str = "B3"

class Asset(SQLModel, table=True):
    ticker: str = Field(primary_key=True)
    name: Optional[str] = None
    price: float
    pe: Optional[float] = None
    dy: Optional[float] = None
    p_vp: Optional[float] = None
    roe: Optional[float] = None
    roic: Optional[float] = None
    ev_ebit: Optional[float] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

sqlite_file_name = "intrinsic.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"
