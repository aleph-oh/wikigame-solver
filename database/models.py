from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from .main import Base

if TYPE_CHECKING:
    from typing import Iterable

__all__ = ["Article", "Link"]


class Link(Base):
    __tablename__ = "link"

    id = Column(Integer, primary_key=True)
    src = Column(Integer, ForeignKey("article.id"), nullable=False)
    dst = Column(Integer, ForeignKey("article.id"), nullable=False)


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    links: Iterable["Link"] = relationship(
        "Link", backref="origin", foreign_keys=[Link.src]
    )
