from typing import Optional
from sqlalchemy.orm import Session as SessionTy

from database import Article

__all__ = ["title_to_id", "id_to_title"]


def title_to_id(db: SessionTy, article_title: str) -> int:
    """
    Map titles of articles to their corresponding ID in the provided database.

    :param db: database session
    :param article_title: title of the article to find the id of
    :return: the id corresponding to the article uniquely named article_name
    :raises ValueError: if n articles have the title article_title for some n != 1
    """
    db_articles: list[Article] = db.query(Article).filter(Article.title == article_title).all()
    if not db_articles:
        raise ValueError(f'No article with title "{article_title}" found in database')
    if len(db_articles) > 1:
        raise ValueError(f'Multiple articles found titled "{article_title}": {db_articles}')
    return db_articles[0].id


def id_to_title(db: SessionTy, article_id: int) -> str:
    """
    Map ids of articles to their corresponding title in the provided database.

    :param db: database session
    :param article_id: id of the article to find the name of
    :return: the name corresponding to the article with the provided id
    :raises ValueError: if no article has the id article_id
    """
    db_article: Optional[Article] = db.query(Article).get(article_id)
    if db_article is None:
        raise ValueError(f"No article with id={article_id} found in database")
    return db_article.title
