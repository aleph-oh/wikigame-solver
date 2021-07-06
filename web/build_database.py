from typing import Iterable, cast

from sqlalchemy.orm import Session as SessionTy

import pywikibot  # type: ignore
from pywikibot.pagegenerators import PreloadingGenerator  # type: ignore
from database import Session, Article, Link
from database.constants import Base, engine

__all__ = ["add_articles_to_db", "clear_db"]


def clear_db() -> None:
    Base.metadata.drop_all(bind=engine, checkfirst=True)
    Base.metadata.create_all(bind=engine, checkfirst=False)


def add_articles_to_db(session: SessionTy = None) -> None:
    if session is None:
        session = Session()
    site = pywikibot.Site("en")
    added_pages: set[int] = set()
    all_pages = site.allpages()
    for _page in PreloadingGenerator(all_pages):
        page = cast(pywikibot.Page, _page)
        if page.pageid in added_pages:
            continue
        added_pages.add(page.pageid)
        linked_pages = cast(Iterable[pywikibot.Page], page.linkedPages())
        db_links: dict[int, tuple[Article, Link]] = {
            linked.pageid: (
                Article(id=linked.pageid, title=linked.title()),
                Link(src=page.pageid, dst=linked.pageid),
            )
            for linked in linked_pages
            if linked.pageid not in added_pages
        }
        added_pages |= db_links.keys()
        db_article = Article(id=page.pageid, title=page.title())
        session.add(db_article)
        for linked_article, link in db_links.values():
            session.add(linked_article)
            session.add(link)
        session.commit()
