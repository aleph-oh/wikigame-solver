from typing import cast

from sqlalchemy.orm import Session as SessionTy

import pywikibot
from database import Session, Article, Link

site = pywikibot.Site("en")
db: SessionTy = Session()
for _page in site.allpages():
    page = cast(pywikibot.Page, _page)
    db_links = [
        Link(src=page.pageid, dst=linked_page.pageid)
        for linked_page in page.linkedPages()
    ]
    db_article = Article(id=page.pageid, title=page.title(), links=db_links)
    db.add(db_article)
    db.commit()
