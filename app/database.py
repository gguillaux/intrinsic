from peewee import SqliteDatabase
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")

db = SqliteDatabase(DB_PATH, pragmas={
    'journal_mode': 'wal',         # Write-Ahead Logging for concurrent reads
    'cache_size': -1024 * 8,       # 8MB cache
    'foreign_keys': 1,
})

def init_db():
    from .models import News, IndexComposition, ParsedMetricsCache
    if db.is_closed():
        db.connect()
    db.create_tables([News, IndexComposition, ParsedMetricsCache])
