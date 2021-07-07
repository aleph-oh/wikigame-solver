#!/usr/bin/env python3
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .constants import Base, engine
from .utilities import set_sqlite_foreign_key_pragma

Base.metadata.create_all(bind=engine)

event.listens_for(Engine, "connect")(set_sqlite_foreign_key_pragma)
