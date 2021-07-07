from contextlib import contextmanager

from hypothesis import strategies as st

from database.constants import Base
from database.test.utilities import TestSession, test_engine

__all__ = ["session_scope", "db_safe_ints"]


db_safe_ints = st.integers(min_value=-1 * 2 ** 63, max_value=2 ** 63 - 1)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    Base.metadata.drop_all(test_engine, checkfirst=True)
    Base.metadata.create_all(test_engine, checkfirst=False)
    session = TestSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        Base.metadata.drop_all(test_engine, checkfirst=True)
        Base.metadata.create_all(test_engine, checkfirst=False)
