# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.
import random
from typing import Mapping, Optional, cast

import pytest

from ..pathfinding import follow_parent_pointers
from hypothesis import example, given, strategies as st

pytestmark = [pytest.mark.game]


@st.composite
def parents_and_dst(draw, max_size=100):
    def replace_one_with_none(d: dict[int, int]) -> Mapping[int, Optional[int]]:
        if not d:
            return d
        result = cast(dict[int, Optional[int]], d) | {
            random.choice(list(d.keys())): None
        }
        return result

    n = draw(
        st.integers(min_value=1, max_value=max_size)
    )
    parents = draw(
        st.fixed_dictionaries(
            {
                i: st.integers(min_value=0, max_value=n - 1).filter(lambda j: i != j)
                for i in range(n)
            }
        ).map(replace_one_with_none)
    )
    dst_id = draw(st.integers(min_value=0, max_value=n - 1))
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
