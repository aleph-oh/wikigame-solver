from sqlite3 import Connection as SQLite3Connection

from .constants import Session

__all__ = ["set_sqlite_foreign_key_pragma"]


def set_sqlite_foreign_key_pragma(conn, _connection_record):
    if isinstance(conn, SQLite3Connection):
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
