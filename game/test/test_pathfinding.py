import random
from typing import Mapping, Optional, cast

import pytest

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
            {
                k: st.sampled_from(keys_list).filter(lambda i: i != k)
                for k in keys
            }
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
