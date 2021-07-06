from typing import Iterable, cast

from sqlalchemy.orm import Session as SessionTy

import pywikibot  # type: ignore
from database import Session, Article, Link

site = pywikibot.Site("en")
db: SessionTy = Session()
for _page in site.allpages():
    page = cast(pywikibot.Page, _page)
    linked_pages = cast(Iterable[pywikibot.Page], page.linkedPages())
    db_links = [
        Link(src=page.pageid, dst=linked_page.pageid) for linked_page in linked_pages
    ]
    db_article = Article(id=page.pageid, title=page.title(), links=db_links)  # type: ignore
    db.add(db_article)
    db.commit()
