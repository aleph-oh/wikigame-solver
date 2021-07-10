"""
This module contains tests for pathfinding functions in the game.pathfinding module.
"""
import json
import os
import random
from typing import Callable, Mapping, Optional, TypeVar, cast

import networkx as nx  # type: ignore
import pytest
from hypothesis import example, given, note, strategies as st
from hypothesis_networkx import graph_builder  # type: ignore
from sqlalchemy.orm import Session

from database import Article, Link
from .utilities import session_scope
from ..pathfinding import bidi_bfs, follow_parent_pointers, multi_target_bfs

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
def nx_graph_and_two_nodes(
    draw: DrawFn, min_nodes=1, max_nodes=10000, min_edges=0, max_edges=500_000, connected=True
) -> tuple[nx.DiGraph, int, int]:
    """
    Generates NetworkX representations of graphs while also returning 2 nodes in the graph.

    :param draw: used to sample values
    :param min_nodes: minimum number of nodes
    :param max_nodes: maximum number of nodes
    :param min_edges: minimum number of edges
    :param max_edges: maximum number of edges
    :param connected: if the graph should be guaranteed to be weakly connected;
                    if True, requires max_edges >= min_nodes - 1
    :return: NetworkX representation of graph, and 2 nodes in that graph
    """
    builder = cast(
        st.SearchStrategy[nx.DiGraph],
        graph_builder(
            min_nodes=min_nodes,
            max_nodes=max_nodes,
            min_edges=min_edges,
            max_edges=max_edges,
            graph_type=nx.DiGraph,
            connected=connected,
        ),
    )
    graph = draw(builder)
    nodes = list(graph.nodes)
    src = draw(st.sampled_from(nodes))
    dst = draw(st.sampled_from(nodes))
    return graph, src, dst


def add_nx_graph_to_db(session: Session, graph: nx.DiGraph) -> None:
    """Add the provided networkx graph to the database attached to ``session``."""
    for n in graph:
        session.add(
            Article(
                id=n, title=str(n), out_links=[Link(src=n, dst=m) for m in graph[n]]
            )  # type: ignore
        )
    session.commit()


def is_valid_path(path: list[str], graph: nx.Graph) -> bool:
    """
    :return: true if all edges in path exist in provided graph, false otherwise
    """
    int_path: list[int] = [int(id_) for id_ in path]
    if not int_path or (len(int_path) == 1 and int_path[0] not in graph):
        return False
    return all((int_path[i], int_path[i + 1]) in graph.edges for i in range(len(int_path) - 1))


def _to_edge_list(adj_list: dict[int, set[int]]) -> list[tuple[int, int]]:
    return [(u, v) for u, vs in adj_list.items() for v in vs]


def _example_from_file(file: str) -> tuple[nx.DiGraph, int, int]:
    with open(os.path.join(os.path.dirname(__file__), file)) as f:
        from_json = json.load(f)
        edge_list = _to_edge_list({int(k): set(v) for k, v in from_json["graph"].items()})
        return nx.DiGraph(edge_list), from_json["src"], from_json["dst"]


def _to_json_example(adj_list: dict[int, list[int]], src: int, dst: int) -> str:
    return json.dumps(
        {"graph": {str(k): sorted(v) for k, v in adj_list.items()}, "src": src, "dst": dst}
    )


@given(inputs=nx_graph_and_two_nodes(connected=False))
def test_multi_nx_equivalent(inputs: tuple[nx.DiGraph, int, int]):
    graph, src, dst = inputs
    adj_list = dict(sorted([(u, sorted(graph[u])) for u in graph]))
    note(f"As JSON example: {_to_json_example(adj_list, src, dst)}")
    with session_scope() as session:
        add_nx_graph_to_db(session, graph)
        multi_target_ppd = multi_target_bfs(session, str(src))
        single_target_via_pp = follow_parent_pointers(dst, multi_target_ppd)
        try:
            nx_path = nx.shortest_path(graph, src, dst)
        except nx.NetworkXNoPath:
            assert single_target_via_pp is None
        else:
            assert single_target_via_pp is not None
            assert is_valid_path(list(map(str, single_target_via_pp)), graph)
            assert len(nx_path) == len(single_target_via_pp)


@given(inputs=nx_graph_and_two_nodes(min_nodes=50, min_edges=250, connected=False))
@example(inputs=_example_from_file("./medium_pathfinding.json"))
def test_bidi_nx_same(inputs: tuple[nx.DiGraph, int, int]) -> None:
    graph, src, dst = inputs
    adj_list = dict(sorted([(u, sorted(graph[u])) for u in graph]))
    note(f"As JSON example: {_to_json_example(adj_list, src, dst)}")
    with session_scope() as session:
        add_nx_graph_to_db(session, graph)
        try:
            nx_path = nx.shortest_path(graph, src, dst)
        except nx.NetworkXNoPath:
            assert bidi_bfs(session, str(src), str(dst)) is None
        else:
            bidi_path = bidi_bfs(session, str(src), str(dst))
            assert bidi_path is not None
            assert is_valid_path(bidi_path, graph)
            assert len(nx_path) == len(bidi_path), (nx_path, bidi_path)
