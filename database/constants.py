"""
This module contains constants useful for interacting with the database.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

MIN_SQLITE_INT: int = -1 * 2 ** 63
MAX_SQLITE_INT: int = 2 ** 63 - 1

__all__ = ["DB_URL", "engine", "Session", "Base", "MIN_SQLITE_INT", "MAX_SQLITE_INT"]

DB_URL = "sqlite:///./wikigame.db"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
