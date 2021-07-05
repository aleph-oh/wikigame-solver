import pytest
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, consumes

pytestmark = [pytest.mark.database]
