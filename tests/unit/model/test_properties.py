"""M1.8 (#14) — property-based hardening of the chain math (F22).

These properties must hold for *all* inputs, not just the fixtures — in particular
the absorption guarantee must survive adversarial probabilities.
"""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from markov_ci.model import (
    EdgeWeight,
    State,
    StateSpace,
    StateType,
    TransitionEdge,
    absorption,
    assemble,
    augment,
    fundamental,
    steps_to_absorb,
)

EDGES = (
    TransitionEdge(source="s0", target="a1"),
    TransitionEdge(source="s0", target="s1"),
    TransitionEdge(source="s1", target="s2"),
    TransitionEdge(source="s1", target="a2"),
    TransitionEdge(source="s2", target="s3"),
    TransitionEdge(source="s3", target="s4"),
    TransitionEdge(source="s3", target="s2", per_attempt=True),
    TransitionEdge(source="s3", target="a2"),
    TransitionEdge(source="s4", target="a1"),
    TransitionEdge(source="s4", target="a2"),
)

_SPACE = StateSpace.of(
    State(id="s0", type=StateType.TRANSIENT),
    State(id="s1", type=StateType.TRANSIENT),
    State(id="s2", type=StateType.TRANSIENT, loop_capable=True),
    State(id="s3", type=StateType.TRANSIENT, loop_capable=True),
    State(id="s4", type=StateType.TRANSIENT),
    State(id="a1", type=StateType.ABSORBING),
    State(id="a2", type=StateType.ABSORBING),
)

_probability = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
_success = st.lists(_probability, min_size=1, max_size=5, unique=False)


def _chain(success: list[float], exit_rate: float, loop_back: float):  # type: ignore[no-untyped-def]
    total = exit_rate + loop_back
    if total > 1.0:
        exit_rate, loop_back = exit_rate / total, loop_back / total
    weights: dict[tuple[str, str], EdgeWeight] = {
        ("s0", "a1"): 0.82,
        ("s0", "s1"): 0.18,
        ("s1", "s2"): 0.75,
        ("s1", "a2"): 0.25,
        ("s2", "s3"): lambda attempt: success[attempt - 1],
        ("s3", "s4"): exit_rate,
        ("s3", "s2"): loop_back,
        ("s3", "a2"): max(0.0, 1.0 - exit_rate - loop_back),
        ("s4", "a1"): 0.90,
        ("s4", "a2"): 0.10,
    }
    return assemble(augment(_SPACE, EDGES, max_attempts=len(success)), weights, sink="a2")


@given(success=_success, exit_rate=_probability, loop_back=_probability)
@settings(max_examples=200, deadline=None)
def test_absorption_probabilities_always_sum_to_one(
    success: list[float], exit_rate: float, loop_back: float,
) -> None:
    chain = _chain(success, exit_rate, loop_back)
    b = absorption(chain)
    assert np.allclose(b.sum(axis=1), 1.0, atol=1e-9)


@given(success=_success, exit_rate=_probability, loop_back=_probability)
@settings(max_examples=200, deadline=None)
def test_fundamental_matrix_is_non_negative_and_finite(
    success: list[float], exit_rate: float, loop_back: float,
) -> None:
    chain = _chain(success, exit_rate, loop_back)
    n = fundamental(chain.Q)
    assert np.all(n >= -1e-9)
    assert np.all(np.isfinite(n))


@given(success=_success, exit_rate=_probability, loop_back=_probability)
@settings(max_examples=200, deadline=None)
def test_steps_to_absorb_are_finite_and_positive(
    success: list[float], exit_rate: float, loop_back: float,
) -> None:
    chain = _chain(success, exit_rate, loop_back)
    t = steps_to_absorb(chain)
    assert np.all(np.isfinite(t))
    assert np.all(t > 0)


@given(max_attempts=st.integers(min_value=1, max_value=6))
@settings(max_examples=50, deadline=None)
def test_adversarial_perfect_success_still_absorbs(max_attempts: int) -> None:
    # success = [1, 1, 1, ...] still terminates: the final attempt has no loop-back
    chain = _chain([1.0] * max_attempts, exit_rate=0.65, loop_back=0.25)
    b = absorption(chain)
    assert np.allclose(b.sum(axis=1), 1.0, atol=1e-9)


@given(success=_success, exit_rate=_probability, loop_back=_probability)
@settings(max_examples=100, deadline=None)
def test_cost_is_monotone_in_the_cost_vector(
    success: list[float], exit_rate: float, loop_back: float,
) -> None:
    chain = _chain(success, exit_rate, loop_back)
    visits = fundamental(chain.Q)
    ones = np.ones(len(chain.transient))
    assert np.all(visits @ (ones * 2.0) >= visits @ ones - 1e-12)
