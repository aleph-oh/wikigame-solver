from typing import Mapping, Optional

from sqlalchemy.orm import Session as SessionTy

from database import Article, Link, Session


def single_target_bfs(
    db: SessionTy, src_title: str, dst_title: str
) -> Optional[list[str]]:
    """

    :param db: database session
    :param src_title: title of the page to start from
    :param dst_title: title of the page to end at
    :return: a shortest path starting from src_title and ending at dst_title,
            or None if no such path exists
    """
    pass


def backtrack(dst_id: int, parents: Mapping[int, Optional[int]]) -> Optional[list[int]]:
    """

    :param dst_id: id of the page the path will end at
    :param parents: parent-pointer mapping from articles to the article which first
                    linked to them; parents[src_id] = None
    :return: a shortest path starting from src_id and ending at dst_id,
            or None if no such path exists
    """
    pass


def title_to_id(db: SessionTy, page_name: str) -> int:
    """

    :param db: database session
    :param page_name: name of the page to find the id of
    :return: the id corresponding to the page uniquely named page_name
    """


def id_to_title(db: SessionTy, page_id: int) -> str:
    """

    :param db: database session
    :param page_id: id of the page to find the name of
    :return: the name corresponding to the page with the provided id
    """
    pass
