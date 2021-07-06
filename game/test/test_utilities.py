# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.
from contextlib import contextmanager

import pytest
from hypothesis import given, reject, strategies as st
from sqlalchemy.orm import Session

from database import Article
from database.constants import Base
from database.test.utilities import TestSession, test_engine

import game.utilities

pytestmark = [pytest.mark.game]


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


def add_article(database_conn: Session, article_id: int, article_title: str) -> None:
    database_conn.add(Article(id=article_id, title=article_title))
    database_conn.commit()


def delete_article(database_conn: Session, article_id: int) -> None:
    article = database_conn.query(Article).get(article_id)
    database_conn.delete(article)
    database_conn.commit()


@given(
    article_id=st.integers(min_value=-1 * 2 ** 63, max_value=2 ** 63 - 1),
    article_title=st.text(),
)
def test_roundtrip_title_to_id_id_to_title(article_id: int, article_title: str):
    with session_scope() as db_conn:
        add_article(db_conn, article_id, article_title)
        try:
            id_from_db = game.utilities.title_to_id(
                db=db_conn, article_title=article_title
            )
        except ValueError:
            reject()
            return
        try:
            title_from_db = game.utilities.id_to_title(
                db=db_conn, article_id=article_id
            )
        except ValueError:
            reject()
            return
        assert article_id == id_from_db, (article_id, id_from_db)
        assert article_title == title_from_db, (article_title, title_from_db)
