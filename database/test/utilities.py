"""
This module contains utilities for testing the database.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ..utilities import set_sqlite_foreign_key_pragma

__all__ = ["TEST_DB_URL", "test_engine", "TestSession"]

TEST_DB_URL = "sqlite:///./test.db"

test_engine = create_engine(TEST_DB_URL)

TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

event.listens_for(Engine, "connect")(set_sqlite_foreign_key_pragma)
