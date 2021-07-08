"""
This module contains the models which declare the structure of the database used for storing
the article graph.
"""
from typing import Iterable

from sqlalchemy import Column, ForeignKey, Integer, Text, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from .constants import Base

__all__ = ["Article", "Link"]


class Link(Base):
    """
    A link between two articles.
    """

    __tablename__ = "link"

    src = Column(Integer, ForeignKey("article.id"), nullable=False)
    dst = Column(Integer, ForeignKey("article.id"), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("src", "dst"),)


class Article(Base):
    """
    A singular article.
    """

    __tablename__ = "article"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    links: Iterable["Link"] = relationship("Link", backref="origin", foreign_keys=[Link.src])
