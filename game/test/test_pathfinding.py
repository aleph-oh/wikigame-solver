"""
This module contains tests for pathfinding functions in the game.pathfinding module.
"""
import random
from typing import Callable, Iterable, Mapping, Optional, TypeVar, cast

import pytest
from hypothesis import example, given, strategies as st
from sqlalchemy.orm import Session

from database import Article, Link
from .utilities import db_safe_ints, session_scope
from ..pathfinding import follow_parent_pointers, bidi_bfs, multi_target_bfs, single_target_bfs

pytestmark = [pytest.mark.game]

Ex = TypeVar("Ex")
DrawFn = Callable[[st.SearchStrategy[Ex]], Ex]


@st.composite
def parents_and_dst(draw: DrawFn, max_size=100) -> tuple[Mapping[int, Optional[int]], int]:
    """
    Generates parent pointer dictionaries for simple graphs and
    a destination to follow parent pointers from.

    :param draw: used to sample values
    :param max_size: maximum size of parent pointer dictionary
    :return: ppd and a node in the ppd
    """

    def replace_one_with_none(d: dict[int, int]) -> Mapping[int, Optional[int]]:
        """
        Return a new dictionary with the same key-value pairs as ``d``, except for one
        key-value pair for which the value is None in the new dictionary.
        If ``d`` is empty, return the empty dictionary.
        """
        if not d:
            return d
        result = cast(dict[int, Optional[int]], d) | {random.choice(list(d.keys())): None}
        return result

    keys: set[int] = draw(st.sets(st.integers(), min_size=1, max_size=max_size))
    keys_list = list(keys)
    parents: Mapping[int, Optional[int]] = draw(
        st.fixed_dictionaries(
            {k: st.sampled_from(keys_list).filter(lambda i: i != k) for k in keys}
        ).map(replace_one_with_none)
    )
    dst_id: int = draw(st.sampled_from(keys_list))
    return parents, dst_id


@given(parents_dst=parents_and_dst())
def test_fuzz_follow_parent_pointers(parents_dst):
    parents, dst_id = parents_dst
    follow_parent_pointers(dst_id=dst_id, parents=parents)


@given(parents_dst=parents_and_dst())
@example(parents_dst=({0: None, 1: 0}, 1))
def test_follow_parent_pointers_recurrence(parents_dst):
    parents, dst_id = parents_dst
    path = follow_parent_pointers(dst_id, parents)
    if (ancestor := parents[dst_id]) is not None:
        parent_path = follow_parent_pointers(ancestor, parents)
        if parent_path is not None:
            assert path == parent_path + [dst_id]
    if path is not None:
        assert len(set(path)) == len(path)


@st.composite
def adjacency_lists(
    draw: DrawFn, min_nodes=0, max_nodes=100, min_edges=0, max_edges=10000
) -> Mapping[int, Iterable[int]]:
    """
    Generates adjacency list representations of graphs, constrained by the properties
    passed in.

    :param draw: used to sample values
    :param min_nodes: minimum number of nodes
    :param max_nodes: maximum number of nodes
    :param min_edges: minimum number of edges
    :param max_edges: maximum number of edges
    :return: adjacency list representation of a graph
    """
    keys: set[int] = draw(
        st.sets(
            db_safe_ints,
            min_size=min_nodes,
            max_size=max_nodes,
        )
    )
    keys_list = list(keys)
    graph = draw(
        st.fixed_dictionaries({k: st.sets(st.sampled_from(keys_list)) for k in keys}).filter(
            lambda d: min_edges <= sum(len(edges) for edges in d.values()) <= max_edges
        )
    )
    return graph


@st.composite
def graph_and_two_nodes(
    draw: DrawFn, min_nodes=1, max_nodes=100, min_edges=0, max_edges=10000
) -> tuple[Mapping[int, Iterable[int]], int, int]:
    """
    Generates adjacency list representations of graphs as in ``adjacency_lists``,
    while also returning two nodes in the graph.

    :param draw: used to sample values
    :param min_nodes: minimum number of nodes
    :param max_nodes: maximum number of nodes
    :param min_edges: minimum number of edges
    :param max_edges: maximum number of edges
    :return: adjacency list representation of a graph, and two not necessarily distinct nodes
             in the graph
    """
    graph = draw(
        adjacency_lists(
            min_nodes=min_nodes,
            max_nodes=max_nodes,
            min_edges=min_edges,
            max_edges=max_edges,
        )
    )
    nodes = list(graph.keys())
    src = draw(st.sampled_from(nodes))
    dst = draw(st.sampled_from(nodes))
    return graph, src, dst


def add_graph_to_db(session: Session, graph: Mapping[int, Iterable[int]]) -> None:
    """Add the provided graph to the database attached to ``session``."""
    for node_id, adjacent in graph.items():
        session.add(
            Article(
                id=node_id,
                title=str(node_id),
                out_links=[Link(src=node_id, dst=other_id) for other_id in adjacent],
                # type: ignore
            )
        )
    session.commit()


@given(inputs=graph_and_two_nodes(max_nodes=25, max_edges=300))
def test_single_multi_target_equivalent(inputs: tuple[Mapping[int, Iterable[int]], int, int]):
    graph, src, dst = inputs
    with session_scope() as session:
        add_graph_to_db(session, graph)
        single_target_result = single_target_bfs(session, str(src), str(dst))
        multi_target_ppd = multi_target_bfs(session, str(src))
        single_target_via_pp = follow_parent_pointers(dst, multi_target_ppd)
        if single_target_result is None:
            assert single_target_via_pp is None
        else:
            assert single_target_via_pp is not None
            assert len(single_target_result) == len(single_target_via_pp)


@given(inputs=graph_and_two_nodes(max_nodes=25, max_edges=300), data=st.data())
def test_single_target_optimal_substructure(
    inputs: tuple[Mapping[int, set[int]], int, int], data: st.DataObject
) -> None:
    graph, src, dst = inputs
    with session_scope() as session:
        add_graph_to_db(session, graph)
        path = single_target_bfs(session, str(src), str(dst))
        if path is None:
            return
        # shortest paths have optimal substructure:
        # if the path is P[0..n], P[i..j] is a shortest path from i to j
        # for all 0 <= i <= j <= n
        sub_start_i = data.draw(
            st.sampled_from(range(len(path))), label="index of start of sub-path"
        )
        sub_end_i = data.draw(
            st.sampled_from(range(sub_start_i, len(path))),
            label="index of end of sub-path",
        )
        sub_src = path[sub_start_i]
        sub_dst = path[sub_end_i]
        subpath = single_target_bfs(session, sub_src, sub_dst)
        assert subpath is not None
        assert len(path[sub_start_i : sub_end_i + 1]) == len(subpath)


@given(inputs=graph_and_two_nodes(max_nodes=25, max_edges=300))
@example(inputs=({0: {0}}, 0, 0))
@example(inputs=({-2: {1}, -1: set(), 0: {2}, 1: {-2, 2}, 2: set(), 3: set()}, 1, 2))
@example(inputs=({-1: {0}, 0: set(), 1: set()}, 1, 0))
def test_uni_bidi_equivalent(inputs: tuple[Mapping[int, Iterable[int]], int, int]) -> None:
    graph, src, dst = inputs
    with session_scope() as session:
        add_graph_to_db(session, graph)
        uni_path = single_target_bfs(session, str(src), str(dst))
        bidi_path = bidi_bfs(session, str(src), str(dst))
        if uni_path is None:
            assert bidi_path is None
        else:
            assert bidi_path is not None, f"Got unidirectional path {uni_path}"
            assert len(uni_path) == len(bidi_path), (uni_path, bidi_path)


@given(inputs=graph_and_two_nodes(max_nodes=25, max_edges=300))
def test_fuzz_bidi(inputs: tuple[Mapping[int, Iterable[int]], int, int]) -> None:
    graph, src, dst = inputs
    with session_scope() as session:
        add_graph_to_db(session, graph)
        # should never throw: src_id and dst_id can be found from given titles
        bidi_bfs(session, str(src), str(dst))
