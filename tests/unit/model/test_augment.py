"""M1.2 (#8) — step augmentation (docs/spec/0001-state-model.md §2, ADR-0002)."""

from __future__ import annotations

import pytest

from markov_ci.model.augment import AugmentedSpace, TransitionEdge, augment
from markov_ci.model.state import InvalidStateSpace, State, StateSpace, StateType


def _base_space() -> StateSpace:
    return StateSpace.of(
        State(id="s0", type=StateType.TRANSIENT),
        State(id="s1", type=StateType.TRANSIENT),
        State(id="s2", type=StateType.TRANSIENT, loop_capable=True),
        State(id="s3", type=StateType.TRANSIENT, loop_capable=True),
        State(id="s4", type=StateType.TRANSIENT),
        State(id="a1", type=StateType.ABSORBING),
        State(id="a2", type=StateType.ABSORBING),
    )


BASE_EDGES = (
    TransitionEdge(source="s1", target="s2"),
    TransitionEdge(source="s2", target="s3"),
    TransitionEdge(source="s3", target="s2", per_attempt=True),
    TransitionEdge(source="s3", target="s4"),
    TransitionEdge(source="s4", target="a1"),
)


def _pairs(aug: AugmentedSpace) -> set[tuple[str, str]]:
    return {(edge.source, edge.target) for edge in aug.edges}


def test_loop_states_expand_to_attempt_indexed_ids() -> None:
    aug = augment(_base_space(), BASE_EDGES, max_attempts=3)
    assert {"s2#1", "s2#2", "s2#3"} <= set(aug.ids)
    assert "s3#1" in aug.ids
    assert "s2" not in aug.ids


def test_non_loop_states_are_unchanged() -> None:
    aug = augment(_base_space(), BASE_EDGES, max_attempts=3)
    for state_id in ("s0", "s1", "s4", "a1", "a2"):
        assert state_id in aug.ids


def test_attempt_groups_are_recorded_in_order() -> None:
    aug = augment(_base_space(), BASE_EDGES, max_attempts=3)
    assert aug.attempt_groups["s2"] == ("s2#1", "s2#2", "s2#3")
    assert aug.attempt_groups["s3"] == ("s3#1", "s3#2", "s3#3")


def test_forward_edge_is_replicated_per_attempt() -> None:
    pairs = _pairs(augment(_base_space(), BASE_EDGES, max_attempts=3))
    assert ("s2#1", "s3#1") in pairs
    assert ("s2#3", "s3#3") in pairs


def test_loop_back_edge_only_below_max_attempts() -> None:
    pairs = _pairs(augment(_base_space(), BASE_EDGES, max_attempts=3))
    assert ("s3#1", "s2#2") in pairs
    assert ("s3#2", "s2#3") in pairs
    # the final attempt has no loop-back — this is the absorption guarantee
    assert ("s3#3", "s2#4") not in pairs
    assert ("s3#3", "s2#3") not in pairs


def test_entry_edge_targets_the_first_attempt() -> None:
    pairs = _pairs(augment(_base_space(), BASE_EDGES, max_attempts=3))
    assert ("s1", "s2#1") in pairs


def test_exit_edge_fans_out_from_every_attempt() -> None:
    pairs = _pairs(augment(_base_space(), BASE_EDGES, max_attempts=3))
    assert ("s3#1", "s4") in pairs
    assert ("s3#3", "s4") in pairs


def test_per_attempt_flag_is_carried_onto_augmented_edges() -> None:
    aug = augment(_base_space(), BASE_EDGES, max_attempts=3)
    back = [e for e in aug.edges if e.source == "s3#1" and e.target == "s2#2"]
    assert back and back[0].per_attempt is True


def test_max_attempts_of_one_has_no_loop_back() -> None:
    aug = augment(_base_space(), BASE_EDGES, max_attempts=1)
    assert not any(e.target.startswith("s2#") for e in aug.edges if e.source.startswith("s3#"))


def test_max_attempts_below_one_is_rejected() -> None:
    with pytest.raises(InvalidStateSpace, match="max_attempts"):
        augment(_base_space(), BASE_EDGES, max_attempts=0)


def test_edge_referencing_unknown_state_is_rejected() -> None:
    with pytest.raises(InvalidStateSpace, match="unknown state"):
        augment(_base_space(), (TransitionEdge(source="s1", target="nope"),), max_attempts=2)


def test_augmentation_is_deterministic() -> None:
    first = augment(_base_space(), BASE_EDGES, max_attempts=3)
    second = augment(_base_space(), BASE_EDGES, max_attempts=3)
    assert first == second
