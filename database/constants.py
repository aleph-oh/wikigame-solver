from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from .utilities import set_sqlite_foreign_key_pragma

MIN_SQLITE_INT: int = -1 * 2 ** 63
MAX_SQLITE_INT: int = 2 ** 63 - 1

__all__ = ["DB_URL", "engine", "Session", "Base", "MIN_SQLITE_INT", "MAX_SQLITE_INT"]

DB_URL = "sqlite:///./wikigame.db"

engine = create_engine(DB_URL)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

event.listens_for(Engine, "connect")(set_sqlite_foreign_key_pragma)
