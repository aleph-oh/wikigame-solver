import random
from typing import Mapping, Optional, cast

import pytest
from sqlalchemy.orm import Session

from database import Article, Link
from .utilities import session_scope
from ..pathfinding import follow_parent_pointers, single_target_bfs, multi_target_bfs
from hypothesis import example, given, strategies as st

pytestmark = [pytest.mark.game]


@st.composite
def parents_and_dst(draw, max_size=100) -> tuple[Mapping[int, Optional[int]], int]:
    def replace_one_with_none(d: dict[int, int]) -> Mapping[int, Optional[int]]:
        if not d:
            return d
        result = cast(dict[int, Optional[int]], d) | {
            random.choice(list(d.keys())): None
        }
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


_db_safe_ints = st.integers(min_value=-1 * 2 ** 63, max_value=2 ** 63 - 1)


@st.composite
def adjacency_lists(
    draw, min_nodes=0, max_nodes=100, min_edges=0, max_edges=10000
) -> Mapping[int, set[int]]:
    keys: set[int] = draw(
        st.sets(
            _db_safe_ints,
            min_size=min_nodes,
            max_size=max_nodes,
        )
    )
    keys_list = list(keys)
    return draw(
        st.fixed_dictionaries(
            {k: st.sets(st.sampled_from(keys_list)) for k in keys}
        ).filter(
            lambda d: min_edges <= sum(len(edges) for edges in d.values()) <= max_edges
        )
    )


@st.composite
def two_nodes_and_graph(
    draw, min_nodes=1, max_nodes=100, min_edges=0, max_edges=10000
) -> tuple[Mapping[int, set[int]], int, int]:
    graph = draw(
        adjacency_lists(
            min_nodes=min_nodes,
            max_nodes=max_nodes,
            min_edges=min_edges,
            max_edges=max_edges,
        )
    )
    nodes = list(graph.keys())
    return draw(
        st.tuples(st.just(graph), st.sampled_from(nodes), st.sampled_from(nodes))
    )


def add_graph_to_db(session: Session, graph: Mapping[int, set[int]]) -> None:
    for node_id, adjacent in graph.items():
        session.add(
            Article(
                id=node_id,
                title=str(node_id),
                links=[Link(src=node_id, dst=other_id) for other_id in adjacent],
                # type: ignore
            )
        )
    session.commit()


@given(inputs=two_nodes_and_graph())
def test_single_multi_target_equivalent(
    inputs: tuple[Mapping[int, set[int]], int, int]
):
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
            assert single_target_result == list(map(str, single_target_via_pp))
