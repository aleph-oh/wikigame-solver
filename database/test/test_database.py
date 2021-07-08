"""
This module consists of tests for the database against a simpler, model implementation.
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from hypothesis import assume, strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

from .constants import TestSession, test_engine
from ..__main__ import Base
from ..constants import MAX_SQLITE_INT, MIN_SQLITE_INT
from ..models import Article, Link

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from typing import Optional

pytestmark = [pytest.mark.database]


@dataclass(unsafe_hash=True, frozen=True)
class MockArticle:
    """Mock database article."""

    id: int
    title: str


@dataclass(frozen=True)
class MockLink:
    """Mock database link."""

    src: int
    dst: int


def init_tables() -> None:
    """
    Re-initialize the test database tables.
    """
    Base.metadata.drop_all(bind=test_engine, checkfirst=True)
    Base.metadata.create_all(bind=test_engine, checkfirst=False)


def is_valid_sqlite_int(n: int) -> bool:
    """
    :return: true if n is an integer which can be inserted into a SQLite database
            as an INTEGER type
    """
    return MIN_SQLITE_INT <= n <= MAX_SQLITE_INT


class DatabaseInteractions(RuleBasedStateMachine):
    """
    A stateful test exercising database operations via the models used to represent an article
    graph.
    """

    def __init__(self) -> None:
        super().__init__()
        self.articles: dict[int, MockArticle] = {}
        self.links: dict[tuple[int, int], MockLink] = {}
        self.assoc_links: dict[MockArticle, set[MockLink]] = defaultdict(set)
        self.db: Session = TestSession()
        init_tables()

    added_articles = Bundle("Articles")
    added_links = Bundle("Links")

    @rule(
        target=added_articles,
        id_=st.integers(min_value=MIN_SQLITE_INT, max_value=MAX_SQLITE_INT),
        title=st.text(),
    )
    def create_article(self, id_: int, title: str) -> MockArticle:
        """
        Create a new article and add it to the database, returning a corresponding mock value
        for storage in the model.

        :param id_: id of the article
        :param title: title of the article
        :return: a mock article with the same field values as those of the inserted article
        """
        assume(id_ not in self.articles)
        article = MockArticle(id=id_, title=title)
        self.articles[id_] = article
        db_article = Article(id=id_, title=title)
        self.db.add(db_article)
        self.db.commit()
        return article

    @rule(
        target=added_links,
        src=added_articles,
        dst=added_articles,
    )
    def create_link(self, src: MockArticle, dst: MockArticle) -> MockLink:
        """
        Create a new link and add it to the database, returning a corresponding mock value
        for storage in the model.

        :param src: origin of the link
        :param dst: destination of the link
        :return: a mock link with same field values as those of the inserted link
        """
        assume((src.id, dst.id) not in self.links)
        assume(src != dst)
        link = MockLink(src=src.id, dst=dst.id)
        self.links[(src.id, dst.id)] = link
        db_link = Link(src=src.id, dst=dst.id)
        self.db.add(db_link)
        self.db.commit()
        self.assoc_links[src].add(link)
        return link

    @rule(article=added_articles)
    def read_article(self, article: MockArticle) -> None:
        """
        Read counterpart to ``article`` from database and check that database performs
        as model expects.
        """
        expected_neighbors = self.assoc_links[article]
        db_article: Optional[Article] = self.db.query(Article).get(article.id)
        assert db_article is not None
        assert expected_neighbors == set(
            map(
                lambda link: MockLink(src=link.src, dst=link.dst),
                db_article.links,
            )
        )

    @rule(link=added_links)
    def read_link(self, link: MockLink) -> None:
        """
        Read counterpart to ``link`` from database and check that database performs
        as model expects.
        """
        db_link: Optional[Link] = self.db.query(Link).get((link.src, link.dst))
        assert db_link is not None
        assert self.links[(link.src, link.dst)].src == db_link.src
        assert self.links[(link.src, link.dst)].dst == db_link.dst

    def teardown(self) -> None:
        """
        Re-initialize tables for next run.
        """
        init_tables()


TestDatabaseInteractions = DatabaseInteractions.TestCase
