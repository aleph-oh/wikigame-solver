# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.
import pytest
from hypothesis import given, reject, strategies as st
from sqlalchemy.orm import Session

from database import Article
from .utilities import db_safe_ints, session_scope

from game.utilities import title_to_id, id_to_title

pytestmark = [pytest.mark.game]


def add_article(database_conn: Session, article_id: int, article_title: str) -> None:
    database_conn.add(Article(id=article_id, title=article_title))
    database_conn.commit()


@given(
    article_id=st.integers(min_value=-1 * 2 ** 63, max_value=2 ** 63 - 1),
    article_title=st.text(),
)
def test_roundtrip_title_to_id_id_to_title(article_id: int, article_title: str):
    with session_scope() as db_conn:
        add_article(db_conn, article_id, article_title)
        try:
            id_from_db = title_to_id(db=db_conn, article_title=article_title)
        except ValueError:
            reject()
            return
        try:
            title_from_db = id_to_title(db=db_conn, article_id=article_id)
        except ValueError:
            reject()
            return
        assert article_id == id_from_db, (article_id, id_from_db)
        assert article_title == title_from_db, (article_title, title_from_db)


@given(title=st.text())
def test_title_to_id_no_matches(title: str):
    with session_scope() as db_conn:
        try:
            title_to_id(db_conn, title)
        except ValueError:
            pass
        else:
            reject()


@given(ids=st.sets(db_safe_ints, min_size=2), title=st.text())
def test_title_to_id_many_matches(ids: set[int], title: str):
    with session_scope() as db_conn:
        for article_id in ids:
            add_article(db_conn, article_id, title)
        try:
            title_to_id(db_conn, title)
        except ValueError:
            pass
        else:
            reject()


@given(article_id=db_safe_ints)
def test_id_to_title_no_matches(article_id: int):
    with session_scope() as db_conn:
        try:
            id_to_title(db_conn, article_id)
        except ValueError:
            pass
        else:
            reject()
