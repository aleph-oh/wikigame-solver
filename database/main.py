from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from .utilities import set_sqlite_foreign_key_pragma

DB_URL = "sqlite:///./wikigame.db"

engine = create_engine(DB_URL)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

Base.metadata.create_all(bind=engine)


event.listens_for(Engine, "connect")(set_sqlite_foreign_key_pragma)
