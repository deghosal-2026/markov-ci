"""M1.5 (#11) — fundamental-matrix operations (docs/spec/0002-matrix-assembly.md §2)."""

from __future__ import annotations

import numpy as np
import pytest

from markov_ci.model.assemble import EdgeWeight, assemble
from markov_ci.model.augment import TransitionEdge, augment
from markov_ci.model.math import (
    absorption,
    expected_cost,
    fundamental,
    split,
    steps_to_absorb,
)
from markov_ci.model.state import State, StateSpace, StateType

SUCCESS = (0.95, 0.95, 0.95)

BASE_EDGES = (
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

WEIGHTS: dict[tuple[str, str], EdgeWeight] = {
    ("s0", "a1"): 0.82,
    ("s0", "s1"): 0.18,
    ("s1", "s2"): 0.75,
    ("s1", "a2"): 0.25,
    ("s2", "s3"): lambda attempt: SUCCESS[attempt - 1],
    ("s3", "s4"): 0.65,
    ("s3", "s2"): 0.25,
    ("s3", "a2"): 0.10,
    ("s4", "a1"): 0.90,
    ("s4", "a2"): 0.10,
}


@pytest.fixture
def chain():  # type: ignore[no-untyped-def]
    space = StateSpace.of(
        State(id="s0", type=StateType.TRANSIENT),
        State(id="s1", type=StateType.TRANSIENT),
        State(id="s2", type=StateType.TRANSIENT, loop_capable=True),
        State(id="s3", type=StateType.TRANSIENT, loop_capable=True),
        State(id="s4", type=StateType.TRANSIENT),
        State(id="a1", type=StateType.ABSORBING),
        State(id="a2", type=StateType.ABSORBING),
    )
    return assemble(augment(space, BASE_EDGES, max_attempts=3), WEIGHTS, sink="a2")


def test_split_returns_q_and_r(chain) -> None:  # type: ignore[no-untyped-def]
    q, r = split(chain)
    assert np.array_equal(q, chain.Q)
    assert np.array_equal(r, chain.R)


def test_fundamental_is_inverse_of_i_minus_q(chain) -> None:  # type: ignore[no-untyped-def]
    n = fundamental(chain.Q)
    identity = np.eye(chain.Q.shape[0])
    assert np.allclose((identity - chain.Q) @ n, identity, atol=1e-9)


def test_fundamental_is_non_negative(chain) -> None:  # type: ignore[no-untyped-def]
    assert np.all(fundamental(chain.Q) >= 0)


def test_absorption_rows_sum_to_one(chain) -> None:  # type: ignore[no-untyped-def]
    b = absorption(chain)
    assert b.shape == (len(chain.transient), len(chain.absorbing))
    assert np.allclose(b.sum(axis=1), 1.0, atol=1e-9)
    assert np.all(b >= -1e-12) and np.all(b <= 1 + 1e-12)


def test_steps_to_absorb_are_finite_and_positive(chain) -> None:  # type: ignore[no-untyped-def]
    t = steps_to_absorb(chain)
    assert t.shape == (len(chain.transient),)
    assert np.all(np.isfinite(t))
    assert np.all(t > 0)


def test_expected_cost_matches_n_times_c(chain) -> None:  # type: ignore[no-untyped-def]
    costs = {state_id: 1.0 for state_id in chain.transient}
    c = expected_cost(chain, costs)
    n = fundamental(chain.Q)
    assert np.allclose(c, n @ np.ones(len(chain.transient)), atol=1e-9)


def test_expected_cost_is_monotone_in_costs(chain) -> None:  # type: ignore[no-untyped-def]
    low = {state_id: 1.0 for state_id in chain.transient}
    high = {state_id: 2.5 for state_id in chain.transient}
    assert np.all(expected_cost(chain, low) < expected_cost(chain, high))


def test_expected_cost_accepts_a_sequence_in_transient_order(chain) -> None:  # type: ignore[no-untyped-def]
    seq = [1.0] * len(chain.transient)
    mapping = dict.fromkeys(chain.transient, 1.0)
    assert np.allclose(
        expected_cost(chain, seq),
        expected_cost(chain, mapping),
        atol=1e-9,
    )


def test_expected_cost_rejects_missing_state(chain) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(KeyError):
        expected_cost(chain, {"s0": 1.0})
