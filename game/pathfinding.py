from collections import deque
from typing import Mapping, Optional, cast

from sqlalchemy.orm import Session as SessionTy

from database import Article
from .utilities import title_to_id, id_to_title

__all__ = ["single_target_bfs", "multi_target_bfs"]

ParentMapping = Mapping[int, Optional[int]]
ParentDict = dict[int, Optional[int]]
IDPath = list[int]
TitlePath = list[str]


def single_target_bfs(
    db: SessionTy, src_title: str, dst_title: str
) -> Optional[TitlePath]:
    """
    Given a graph represented in the database which session ``db`` accesses, find the shortest
    path from the article with title ``src_title`` to the article with title ``dst_title``, or
    None if no such path exists.

    :param db: database session
    :param src_title: title of the article to start from
    :param dst_title: title of the article to end at
    :return: a shortest path starting from src_title and ending at dst_title,
            or None if no such path exists
    """
    src_id = title_to_id(db, src_title)
    dst_id = title_to_id(db, dst_title)
    parents: ParentDict = {src_id: None}
    q: deque[int] = deque([src_id])
    while q and dst_id not in parents:
        q, parents = _bfs_update_step(db, q, parents)
    if dst_id not in parents:
        return None
    assert parents[src_id] is None
    shortest_path = follow_parent_pointers(dst_id, parents)
    assert shortest_path is not None
    return [id_to_title(db, id_) for id_ in shortest_path]


def multi_target_bfs(db: SessionTy, src_title: str) -> ParentMapping:
    """
    Given a graph represented in the database which session ``db`` accesses, find the shortest
    path from the article with title ``src_title`` to all other reachable articles,
    represented via the returned parent mapping.

    :param db: database session
    :param src_title: title of the article to start from
    :return: a mapping from articles to their ancestors in the shortest path from the article
            with title src_title
    """
    src_id = title_to_id(db, src_title)
    parents: ParentDict = {src_id: None}
    q: deque[int] = deque([src_id])
    while q:
        q, parents = _bfs_update_step(db, q, parents)
    assert parents[src_id] is None
    return parents


def _bfs_update_step(
    db: SessionTy, q: deque[int], parents: ParentDict
) -> tuple[deque[int], ParentDict]:
    to_expand = q.popleft()
    db_article: Optional[Article] = db.query(Article).get(to_expand)
    assert db_article is not None
    unseen_articles: set[int] = {
        link.dst for link in db_article.links if link.dst not in parents
    }
    parents |= {unseen: to_expand for unseen in unseen_articles}
    q.extend(unseen_articles)
    return q, parents


def follow_parent_pointers(dst_id: int, parents: ParentMapping) -> Optional[IDPath]:
    """
    Given a parent-pointer mapping ``parent``, find a shortest path starting from ``src_id``
    and ending at ``dst_id``, or None if no such path exists.

    :param dst_id: id of the article the path will end at
                    requires dst_id in parents
    :param parents: parent-pointer mapping from articles to the article which first
                    linked to them; parents[src_id] = None
                    requires v in parents for all v in parents
    :return: a shortest path starting from src_id and ending at dst_id,
            or None if no such path exists

    >>> parent_map = {0: None, 1: 0, 2: 0, 3: 1, 4: 2, 5: 3}
    >>> follow_parent_pointers(0, parent_map)
    [0]
    >>> follow_parent_pointers(1, parent_map)
    [0, 1]
    >>> follow_parent_pointers(2, parent_map)
    [0, 2]
    >>> follow_parent_pointers(3, parent_map)
    [0, 1, 3]
    >>> follow_parent_pointers(4, parent_map)
    [0, 2, 4]
    >>> follow_parent_pointers(5, parent_map)
    [0, 1, 3, 5]
    >>> all(follow_parent_pointers(dst, parent_map) ==
    ...     follow_parent_pointers(parent_map[dst], parent_map) + [dst]
    ...     for dst in range(1, 6))
    True
    """
    assert dst_id in parents
    assert all(ancestor is None or ancestor in parents for ancestor in parents.values())
    curr: int = dst_id
    path = [curr]
    while parents[curr] is not None:
        curr = cast(int, parents[curr])
        path.append(curr)
        if len(parents) < len(path):
            return None
    return path[::-1]
