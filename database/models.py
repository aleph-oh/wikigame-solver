from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from .main import Base

__all__ = [
    "Article",
    "Link"
]


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    links = relationship("Links", back_ref="src")


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    src = Column(Integer, ForeignKey("Article.id"))
    dst = Column(Integer, ForeignKey("Article.id"))
