from peewee import SqliteDatabase
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")

db = SqliteDatabase(DB_PATH)

def init_db():
    from .models import News, IndexComposition, ParsedMetricsCache
    db.connect()
    db.create_tables([News, IndexComposition, ParsedMetricsCache])
