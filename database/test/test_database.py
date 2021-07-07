from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from hypothesis import assume, strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

from .utilities import TestSession, test_engine
from ..__main__ import Base
from ..constants import MAX_SQLITE_INT, MIN_SQLITE_INT
from ..models import Article, Link

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from typing import Optional

pytestmark = [pytest.mark.database]


@dataclass(unsafe_hash=True, frozen=True)
class MockArticle:
    id: int
    title: str


@dataclass(unsafe_hash=True, frozen=True)
class MockLink:
    id: int
    src: int
    dst: int


def init_tables() -> None:
    Base.metadata.drop_all(bind=test_engine, checkfirst=True)
    Base.metadata.create_all(bind=test_engine, checkfirst=False)


def is_valid_sqlite_int(n: int) -> bool:
    return MIN_SQLITE_INT <= n <= MAX_SQLITE_INT


class DatabaseInteractions(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.articles: dict[int, MockArticle] = {}
        self.links: dict[int, MockLink] = {}
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
    def create_article(self, id_: int, title: str):
        assume(id_ not in self.articles)
        article = MockArticle(id=id_, title=title)
        self.articles[id_] = article
        db_article = Article(id=id_, title=title)
        self.db.add(db_article)
        self.db.commit()
        return article

    @rule(
        target=added_links,
        id_=st.integers(min_value=MIN_SQLITE_INT, max_value=MAX_SQLITE_INT),
        src=added_articles,
        dst=added_articles,
    )
    def create_link(self, id_: int, src: MockArticle, dst: MockArticle):
        assume(id_ not in self.links)
        assume(src != dst)
        link = MockLink(id=id_, src=src.id, dst=dst.id)
        self.links[id_] = link
        db_link = Link(id=id_, src=src.id, dst=dst.id)
        self.db.add(db_link)
        self.db.commit()
        self.assoc_links[src].add(link)
        return link

    @rule(article=added_articles)
    def read_article(self, article: MockArticle):
        expected_neighbors = self.assoc_links[article]
        db_article: Optional[Article] = self.db.query(Article).get(article.id)
        assert db_article is not None
        assert expected_neighbors == set(
            map(
                lambda link: MockLink(id=link.id, src=link.src, dst=link.dst),
                db_article.links,
            )
        )

    @rule(link=added_links)
    def read_link(self, link: MockLink):
        db_link: Optional[Link] = self.db.query(Link).get(link.id)
        assert db_link is not None
        assert self.links[link.id].src == db_link.src
        assert self.links[link.id].dst == db_link.dst

    def teardown(self):
        init_tables()


TestDatabaseInteractions = DatabaseInteractions.TestCase
