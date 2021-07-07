"""
This module contains schemas for providing responses to API requests.
"""
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ArticleWrapper(BaseModel):
    """A wrapper for articles containing additional information beyond their title alone."""

    id: int
    title: str
    link: HttpUrl


class ArticlePath(BaseModel):
    """A path of articles connected by links on each page."""

    articles: list[ArticleWrapper] = Field(min_items=1)


class ManyArticlePaths(BaseModel):
    """
    A mapping from articles to paths between them and a source article, or None if no such
    path exists.
    """

    paths: dict[str, Optional[ArticlePath]]
