from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from ..main import Base
from ..utilities import set_sqlite_foreign_key_pragma

TEST_DB_URL = "sqlite:///./test.db"

test_engine = create_engine(TEST_DB_URL)

TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

event.listens_for(Engine, "connect")(set_sqlite_foreign_key_pragma)
