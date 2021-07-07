from typing import Optional

from pydantic import BaseModel, Field, conlist, HttpUrl


class ArticleWrapper(BaseModel):
    id: int
    title: str
    link: HttpUrl


class ArticlePath(BaseModel):
    articles: list[ArticleWrapper] = Field(min_items=1)


class ManyArticlePaths(BaseModel):
    paths: dict[str, Optional[ArticlePath]]
