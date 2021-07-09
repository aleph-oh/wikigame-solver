"""
This module contains pathfinding functions which use the article graph database for finding
shortest paths between articles.
"""
from collections import deque
from typing import Literal, Mapping, Optional, cast

from sqlalchemy.orm import Session as SessionTy

from database import Article
from .utilities import id_to_title, title_to_id

__all__ = ["single_target_bfs", "bidi_bfs", "multi_target_bfs", "follow_parent_pointers"]

ParentMapping = Mapping[int, Optional[int]]
ParentDict = dict[int, Optional[int]]
IDPath = list[int]
TitlePath = list[str]


def single_target_bfs(db: SessionTy, src_title: str, dst_title: str) -> Optional[TitlePath]:
    """
    Given a graph represented in the database which session ``db`` accesses, find the shortest
    path from the article with title ``src_title`` to the article with title ``dst_title``, or
    None if no such path exists.

    :param db: database session
    :param src_title: title of the article to start from
    :param dst_title: title of the article to end at
    :return: a shortest path starting from src_title and ending at dst_title,
            or None if no such path exists
    :raises ValueError: if either src_id or dst_id cannot be found from a title
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


def bidi_bfs(db: SessionTy, src_title: str, dst_title: str) -> Optional[TitlePath]:
    if src_title == dst_title:
        return [src_title]
    src_id = title_to_id(db, src_title)
    dst_id = title_to_id(db, dst_title)
    fwd_parents: ParentDict = {src_id: None}
    rev_children: ParentDict = {dst_id: None}
    fwq_q = deque([src_id])
    rev_q = deque([dst_id])
    done = False
    while fwq_q and rev_q:
        # TODO: refactor this to clean it up; basically identical code here
        if done:
            break
        article_id = fwq_q.popleft()
        db_article: Optional[Article] = db.query(Article).get(article_id)
        assert db_article is not None
        for link in db_article.out_links:
            linked_to = link.dst
            if linked_to in rev_children:
                fwd_parents[linked_to] = article_id
                done = True
                break
            elif linked_to not in fwd_parents:
                fwd_parents[linked_to] = article_id
                fwq_q.append(linked_to)
        if done:
            break
        article_id = rev_q.popleft()
        db_article = db.query(Article).get(article_id)
        assert db_article is not None
        for link in db_article.in_links:
            linked_from = link.src
            if linked_from in fwd_parents:
                rev_children[linked_from] = article_id
                done = True
                break
            elif linked_from not in rev_children:
                rev_children[linked_from] = article_id
                rev_q.append(linked_from)
    else:
        if dst_id in fwd_parents:
            path = follow_parent_pointers(dst_id, fwd_parents)
            if path is None:
                return None
            return _id_path_to_title_path(db, path)
        if src_id in rev_children:
            path = follow_parent_pointers(src_id, rev_children)
            if path is None:
                return None
            return _id_path_to_title_path(db, path[::-1])
    common = fwd_parents.keys() & rev_children.keys()
    if not common:
        return None
    assert (
        fwd_parents[src_id] is None and rev_children[dst_id] is None
    ), "expected not to assign to already-initialized values"
    common_node = common.pop()
    src_to_common = follow_parent_pointers(common_node, fwd_parents)
    if src_to_common is None:
        return None
    common_to_dst = follow_parent_pointers(common_node, rev_children)
    if common_to_dst is None:
        return None
    shortest_path = src_to_common[:-1] + common_to_dst[::-1]
    return _id_path_to_title_path(db, shortest_path)


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


def _id_path_to_title_path(db: SessionTy, id_path: list[int]) -> list[str]:
    return [id_to_title(db, id_) for id_ in id_path]


def _bfs_update_step(
    db: SessionTy, q: deque[int], parents: ParentDict
) -> tuple[deque[int], ParentDict]:
    to_expand = q.popleft()
    db_article: Optional[Article] = db.query(Article).get(to_expand)
    assert db_article is not None
    unseen_articles: set[int] = {
        link.dst for link in db_article.out_links if link.dst not in parents
    }
    parents |= {unseen: to_expand for unseen in unseen_articles}
    q.extend(unseen_articles)
    return q, parents


def follow_parent_pointers(dst_id: int, parents: ParentMapping) -> Optional[IDPath]:
    """
    Given a parent-pointer mapping ``parents``, find a shortest path starting from ``src_id``
    and ending at ``dst_id``, or None if no such path exists.

    :param dst_id: id of the article the path will end at
    :param parents: parent-pointer mapping from articles to the article which first
                    linked to them; parents[src_id] = None
                    requires v in parents.keys() for all v in parents.values()
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
    >>> follow_parent_pointers(7, parent_map)
    """
    if dst_id not in parents:
        return None
    assert all(ancestor is None or ancestor in parents for ancestor in parents.values())
    curr: int = dst_id
    path = [curr]
    while parents[curr] is not None:
        curr = cast(int, parents[curr])
        path.append(curr)
        if len(parents) < len(path):
            return None
    return path[::-1]
