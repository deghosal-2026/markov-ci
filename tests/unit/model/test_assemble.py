"""M1.3 (#9) — matrix assembly (docs/spec/0002-matrix-assembly.md §1)."""

from __future__ import annotations

import numpy as np
import pytest

from markov_ci.model.assemble import EdgeWeight, assemble
from markov_ci.model.augment import TransitionEdge, augment
from markov_ci.model.state import InvalidStateSpace, State, StateSpace, StateType

SUCCESS = (0.92, 0.65, 0.20)

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


def _space() -> StateSpace:
    return StateSpace.of(
        State(id="s0", type=StateType.TRANSIENT),
        State(id="s1", type=StateType.TRANSIENT),
        State(id="s2", type=StateType.TRANSIENT, loop_capable=True),
        State(id="s3", type=StateType.TRANSIENT, loop_capable=True),
        State(id="s4", type=StateType.TRANSIENT),
        State(id="a1", type=StateType.ABSORBING),
        State(id="a2", type=StateType.ABSORBING),
    )


def _chain(max_attempts: int = 3):  # type: ignore[no-untyped-def]
    augmented = augment(_space(), BASE_EDGES, max_attempts=max_attempts)
    return assemble(augmented, WEIGHTS, sink="a2")


def test_transients_precede_absorbing_states() -> None:
    chain = _chain()
    assert chain.transient + chain.absorbing == chain.states
    assert set(chain.absorbing) == {"a1", "a2"}
    assert "s0" in chain.transient and "s4" in chain.transient


def test_every_row_sums_to_one() -> None:
    chain = _chain()
    assert np.allclose(chain.P.sum(axis=1), 1.0, atol=1e-9)


def test_absorbing_rows_are_identity() -> None:
    chain = _chain()
    for state_id in chain.absorbing:
        row = chain.P[chain.index[state_id]]
        assert row[chain.index[state_id]] == pytest.approx(1.0)
        assert row.sum() == pytest.approx(1.0)


def test_q_and_r_shapes() -> None:
    chain = _chain()
    t = len(chain.transient)
    r = len(chain.absorbing)
    assert chain.Q.shape == (t, t)
    assert chain.R.shape == (t, r)


def test_per_attempt_success_is_applied_per_attempt() -> None:
    chain = _chain()
    p = chain.P
    assert p[chain.index["s2#1"], chain.index["s3#1"]] == pytest.approx(0.92)
    assert p[chain.index["s2#2"], chain.index["s3#2"]] == pytest.approx(0.65)
    assert p[chain.index["s2#3"], chain.index["s3#3"]] == pytest.approx(0.20)


def test_final_attempt_mass_renormalizes_into_the_sink() -> None:
    # s3#3 has no loop-back, so its 0.25 must land in a2: 0.10 + 0.25 = 0.35
    chain = _chain()
    assert chain.P[chain.index["s3#3"], chain.index["a2"]] == pytest.approx(0.35)
    # non-final attempts keep the 0.10 escape
    assert chain.P[chain.index["s3#1"], chain.index["a2"]] == pytest.approx(0.10)


def test_remainder_routes_to_the_sink() -> None:
    # s2#k -> a2 is the remainder: 1 - success[k]
    chain = _chain()
    assert chain.P[chain.index["s2#1"], chain.index["a2"]] == pytest.approx(0.08)
    assert chain.P[chain.index["s2#3"], chain.index["a2"]] == pytest.approx(0.80)


def test_max_attempts_one_is_absorbing() -> None:
    chain = _chain(max_attempts=1)
    assert np.allclose(chain.P.sum(axis=1), 1.0, atol=1e-9)
    # with a single attempt there is no loop-back at all
    assert chain.P[chain.index["s3#1"], chain.index["a2"]] == pytest.approx(0.35)


def test_missing_probability_is_rejected() -> None:
    augmented = augment(_space(), BASE_EDGES, max_attempts=3)
    with pytest.raises(InvalidStateSpace, match="no probability"):
        assemble(augmented, {}, sink="a2")


def test_unknown_sink_is_rejected() -> None:
    augmented = augment(_space(), BASE_EDGES, max_attempts=3)
    with pytest.raises(InvalidStateSpace):
        assemble(augmented, WEIGHTS, sink="does-not-exist")
