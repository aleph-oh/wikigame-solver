#!usr/bin/env python3
from .build_database import populate_db, clear_db

if __name__ == "__main__":
    clear_db()
    populate_db()
