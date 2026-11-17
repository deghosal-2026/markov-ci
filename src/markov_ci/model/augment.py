"""Step augmentation (docs/spec/0001-state-model.md §2, ADR-0002).

Loop-capable transient states are expanded into attempt-indexed states
(``s2#1``, ``s2#2`` …) so per-attempt decay is expressed as ordinary Markov
edges. This is what keeps the chain genuinely Markov — and therefore what keeps
the closed-form results (``N``, ``B``, ``t``, ``C``) exact.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from markov_ci.model.state import InvalidStateSpace, State, StateSpace


@dataclass(frozen=True, slots=True)
class TransitionEdge:
    """A structural edge between base states (probabilities arrive in assembly)."""

    source: str
    target: str
    per_attempt: bool = False


@dataclass(frozen=True, slots=True)
class AugmentedEdge:
    """An edge on the attempt-augmented state space."""

    source: str
    target: str
    base_source: str
    base_target: str
    attempt: int
    per_attempt: bool


@dataclass(frozen=True, slots=True)
class AugmentedSpace:
    """The attempt-expanded state space and its edges."""

    states: tuple[State, ...]
    edges: tuple[AugmentedEdge, ...]
    attempt_groups: dict[str, tuple[str, ...]]
    max_attempts: int

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(state.id for state in self.states)

    def get(self, state_id: str) -> State:
        for state in self.states:
            if state.id == state_id:
                return state
        raise InvalidStateSpace(f"unknown augmented state id: {state_id!r}")


def augment(
    space: StateSpace,
    edges: Sequence[TransitionEdge],
    max_attempts: int,
) -> AugmentedSpace:
    """Expand loop-capable states to ``name#attempt`` and rewrite edges.

    Within the loop set, an edge to a state declared *later* is a forward edge
    (attempt ``k`` → attempt ``k``); an edge to a state declared *earlier* is a
    loop-back (attempt ``k`` → attempt ``k+1``). On the final attempt the loop-back
    edge is dropped — that is the absorption guarantee (ADR-0004).
    """
    if max_attempts < 1:
        raise InvalidStateSpace(f"max_attempts must be >= 1, got {max_attempts}")

    loop_order = {
        state.id: index
        for index, state in enumerate(space.states)
        if state.loop_capable
    }

    attempt_groups: dict[str, tuple[str, ...]] = {}
    augmented_states: list[State] = []
    for state in space.states:
        if state.loop_capable:
            expanded = tuple(f"{state.id}#{k}" for k in range(1, max_attempts + 1))
            attempt_groups[state.id] = expanded
            augmented_states.extend(
                State(id=expanded_id, type=state.type)
                for expanded_id in expanded
            )
        else:
            augmented_states.append(state)

    augmented_edges: list[AugmentedEdge] = []
    for edge in edges:
        if edge.source not in space:
            raise InvalidStateSpace(f"edge references unknown state: {edge.source!r}")
        if edge.target not in space:
            raise InvalidStateSpace(f"edge references unknown state: {edge.target!r}")

        source_is_loop = edge.source in attempt_groups
        target_is_loop = edge.target in attempt_groups

        if not source_is_loop and not target_is_loop:
            _append(augmented_edges, edge, edge.source, edge.target, attempt=1)
        elif not source_is_loop and target_is_loop:
            first = attempt_groups[edge.target][0]
            _append(augmented_edges, edge, edge.source, first, attempt=1)
        elif source_is_loop and not target_is_loop:
            for attempt, source_id in enumerate(attempt_groups[edge.source], start=1):
                _append(augmented_edges, edge, source_id, edge.target, attempt)
        elif loop_order[edge.target] > loop_order[edge.source]:
            # forward edge: attempt k → attempt k
            for attempt, source_id in enumerate(attempt_groups[edge.source], start=1):
                target_id = attempt_groups[edge.target][attempt - 1]
                _append(augmented_edges, edge, source_id, target_id, attempt)
        else:
            # loop-back: attempt k → attempt k+1, dropped on the final attempt
            for attempt, source_id in enumerate(attempt_groups[edge.source], start=1):
                if attempt < max_attempts:
                    target_id = attempt_groups[edge.target][attempt]
                    _append(augmented_edges, edge, source_id, target_id, attempt)

    return AugmentedSpace(
        states=tuple(augmented_states),
        edges=tuple(augmented_edges),
        attempt_groups=attempt_groups,
        max_attempts=max_attempts,
    )


def _append(
    edges: list[AugmentedEdge],
    base: TransitionEdge,
    source: str,
    target: str,
    attempt: int,
) -> None:
    edges.append(
        AugmentedEdge(
            source=source,
            target=target,
            base_source=base.source,
            base_target=base.target,
            attempt=attempt,
            per_attempt=base.per_attempt,
        ),
    )
