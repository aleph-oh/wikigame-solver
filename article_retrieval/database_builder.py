"""
This module contains methods used for populating and constructing the article graph database.
"""
from typing import Iterable, cast

import pywikibot  # type: ignore
from pywikibot.pagegenerators import PreloadingGenerator  # type: ignore
from sqlalchemy.orm import Session as SessionTy

from database import Article, Link, Session

__all__ = ["populate_db"]


def populate_db(session: SessionTy = None) -> None:
    """
    Populate the database which ``session`` can modify to act as a graph, with articles
    as nodes and links between articles as uni-directional edges.

    :param session: database session
    """
    if session is None:
        session = Session()
    site = pywikibot.Site("en")
    added_pages: set[int] = set()
    all_pages = site.allpages()
    for _page in PreloadingGenerator(all_pages):
        page = cast(pywikibot.Page, _page)
        if page.pageid not in added_pages:
            session.add(Article(id=page.pageid, title=page.title()))
            added_pages.add(page.pageid)
        linked_pages: set[Article] = {
            Article(id=linked.pageid, title=linked.title())
            for linked in cast(Iterable[pywikibot.Page], page.linkedPages())
            if linked.pageid not in added_pages
        }
        links: set[Link] = {
            Link(src=page.pageid, dst=linked.pageid)
            for linked in cast(Iterable[pywikibot.Page], page.linkedPages())
        }
        for linked_page in linked_pages:
            session.add(linked_page)
            added_pages.add(linked_page.id)
        for link in links:
            session.add(link)
        session.commit()
