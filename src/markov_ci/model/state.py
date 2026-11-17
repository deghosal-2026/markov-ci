"""State primitives for the Markov model (docs/spec/0001-state-model.md §1).

A `StateSpace` is an ordered collection of `State`s partitioned into *transient*
states (the run can leave them) and *absorbing* states (terminal — once entered,
never left). This module is intentionally dependency-free so the rest of the model
can build on it without pulling in numpy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class InvalidStateSpace(ValueError):
    """Raised when a state or state space is malformed."""


class StateType(StrEnum):
    """Whether a state can be left."""

    TRANSIENT = "transient"
    ABSORBING = "absorbing"


@dataclass(frozen=True, slots=True)
class State:
    """A single node in the chain.

    `loop_capable` marks a transient state that the step-augmentation step
    (spec 0001 §2) will expand into attempt-indexed states such as ``s2#1``.
    """

    id: str
    type: StateType
    loop_capable: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise InvalidStateSpace("state id must be non-empty")
        if self.type is StateType.ABSORBING and self.loop_capable:
            raise InvalidStateSpace(
                f"absorbing state {self.id!r} cannot be loop_capable",
            )

    @property
    def is_absorbing(self) -> bool:
        return self.type is StateType.ABSORBING


@dataclass(frozen=True, slots=True)
class StateSpace:
    """An ordered, validated collection of states."""

    states: tuple[State, ...]

    @classmethod
    def of(cls, *states: State) -> StateSpace:
        """Build and validate a state space from the given states, in order."""
        space = cls(states=tuple(states))
        space.validate()
        return space

    def validate(self) -> None:
        """Raise `InvalidStateSpace` if the space is malformed."""
        ids = [state.id for state in self.states]
        duplicates = sorted({state_id for state_id in ids if ids.count(state_id) > 1})
        if duplicates:
            raise InvalidStateSpace(f"duplicate state ids: {duplicates}")
        if not self.absorbing:
            raise InvalidStateSpace(
                "state space must contain at least one absorbing state",
            )

    @property
    def transients(self) -> tuple[State, ...]:
        return tuple(state for state in self.states if not state.is_absorbing)

    @property
    def absorbing(self) -> tuple[State, ...]:
        return tuple(state for state in self.states if state.is_absorbing)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(state.id for state in self.states)

    def get(self, state_id: str) -> State:
        for state in self.states:
            if state.id == state_id:
                return state
        raise InvalidStateSpace(f"unknown state id: {state_id!r}")

    def __contains__(self, state_id: object) -> bool:
        return any(state.id == state_id for state in self.states)

    def __len__(self) -> int:
        return len(self.states)
