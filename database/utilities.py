"""
This module contains utilities for initializing and interacting with the database which is
used to store the article graph.
"""
from sqlite3 import Connection as SQLite3Connection

from sqlalchemy.engine import Engine

from .constants import Base, Session

__all__ = ["set_sqlite_foreign_key_pragma", "get_db", "clear_db"]


def set_sqlite_foreign_key_pragma(conn, _connection_record):
    """
    If using SQLite, enable foreign keys.
    :param conn: database connection
    :param _connection_record: unused param
    """
    if isinstance(conn, SQLite3Connection):
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db():
    """
    Return a generator which provides a session interfacing with the production database.
    """
    db = Session()
    try:
        yield db
    finally:
        db.close()


def clear_db(engine: Engine) -> None:
    """Drop and recreate all tables in the database with engine ``engine``."""
    Base.metadata.drop_all(bind=engine, checkfirst=True)
    Base.metadata.create_all(bind=engine, checkfirst=False)
