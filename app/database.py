from sqlmodel import Session, create_engine, SQLModel
from app.models import sqlite_url

engine = create_engine(sqlite_url, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
