#!/usr/bin/env python3
"""Constructs article graph."""
from database import clear_db
from database.constants import engine
from .database_builder import populate_db

clear_db(engine)
populate_db()
