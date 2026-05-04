from peewee import Model, CharField, DateTimeField, FloatField, TextField
from .database import db
import datetime

class BaseModel(Model):
    class Meta:
        database = db

class News(BaseModel):
    title = CharField()
    link = CharField(unique=True)
    published_at = DateTimeField(default=datetime.datetime.now)
    source = CharField()

class IndexComposition(BaseModel):
    index_name = CharField()  # e.g., 'IBOV', 'IFIX'
    ticker = CharField()
    weight = FloatField()
    last_updated = DateTimeField(default=datetime.datetime.now)

    class Meta:
        indexes = (
            (('index_name', 'ticker'), True),
        )

class ParsedMetricsCache(BaseModel):
    ticker = CharField(unique=True)
    data = TextField()
    last_updated = DateTimeField(default=datetime.datetime.now)
