"""M1.1 (#7) — State, StateType, StateSpace (docs/spec/0001-state-model.md §1)."""

from __future__ import annotations

import pytest

from markov_ci.model.state import (
    InvalidStateSpace,
    State,
    StateSpace,
    StateType,
)


def _space(*states: State) -> StateSpace:
    return StateSpace.of(*states)


def test_state_type_values() -> None:
    assert StateType.TRANSIENT.value == "transient"
    assert StateType.ABSORBING.value == "absorbing"


def test_state_defaults_to_not_loop_capable() -> None:
    state = State(id="s0", type=StateType.TRANSIENT)
    assert state.loop_capable is False
    assert state.is_absorbing is False


def test_absorbing_state_is_flagged_absorbing() -> None:
    assert State(id="a1", type=StateType.ABSORBING).is_absorbing is True


def test_state_id_must_be_non_empty() -> None:
    with pytest.raises(InvalidStateSpace, match="non-empty"):
        State(id="", type=StateType.TRANSIENT)


def test_absorbing_state_cannot_be_loop_capable() -> None:
    with pytest.raises(InvalidStateSpace, match="loop_capable"):
        State(id="a1", type=StateType.ABSORBING, loop_capable=True)


def test_statespace_partitions_transients_and_absorbing() -> None:
    space = _space(
        State(id="s0", type=StateType.TRANSIENT),
        State(id="s2", type=StateType.TRANSIENT, loop_capable=True),
        State(id="a1", type=StateType.ABSORBING),
    )
    assert [s.id for s in space.transients] == ["s0", "s2"]
    assert [s.id for s in space.absorbing] == ["a1"]


def test_statespace_rejects_duplicate_ids() -> None:
    with pytest.raises(InvalidStateSpace, match="duplicate"):
        _space(
            State(id="s0", type=StateType.TRANSIENT),
            State(id="s0", type=StateType.TRANSIENT),
            State(id="a1", type=StateType.ABSORBING),
        )


def test_statespace_requires_at_least_one_absorbing_state() -> None:
    with pytest.raises(InvalidStateSpace, match="absorbing"):
        _space(State(id="s0", type=StateType.TRANSIENT))


def test_get_returns_the_state() -> None:
    space = _space(
        State(id="s0", type=StateType.TRANSIENT),
        State(id="a1", type=StateType.ABSORBING),
    )
    assert space.get("s0").type is StateType.TRANSIENT


def test_get_unknown_id_raises() -> None:
    space = _space(
        State(id="s0", type=StateType.TRANSIENT),
        State(id="a1", type=StateType.ABSORBING),
    )
    with pytest.raises(InvalidStateSpace, match="unknown state id"):
        space.get("nope")


def test_contains_and_len_and_ids() -> None:
    space = _space(
        State(id="s0", type=StateType.TRANSIENT),
        State(id="a1", type=StateType.ABSORBING),
    )
    assert "s0" in space
    assert "nope" not in space
    assert len(space) == 2
    assert space.ids == ("s0", "a1")


def test_statespace_is_immutable_ordered() -> None:
    states = (
        State(id="s0", type=StateType.TRANSIENT),
        State(id="a1", type=StateType.ABSORBING),
    )
    assert _space(*states).states == states
