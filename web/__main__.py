#!usr/bin/env python3
from .build_database import add_articles_to_db, clear_db

if __name__ == "__main__":
    clear_db()
    add_articles_to_db()
