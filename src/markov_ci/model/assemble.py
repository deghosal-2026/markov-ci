"""Matrix assembly (docs/spec/0002-matrix-assembly.md §1).

Given an attempt-augmented state space and a weight for each base edge, build the
canonical transition matrix ``P = [[Q, R], [0, I]]``.

Two mechanics carry the product's guarantees:

* a transient row is normalized by routing any *remainder* mass to a designated
  sink state — this is how ``s2#k -> a2`` gets ``1 - success[k]``;
* on the final attempt the loop-back edge is already absent (augmentation), so the
  remainder mechanism renormalizes the freed probability into the sink — this is
  the absorption guarantee made arithmetic (ADR-0004).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from markov_ci.model.augment import AugmentedSpace
from markov_ci.model.state import InvalidStateSpace

EdgeWeight = float | Callable[[int], float]

_TOL = 1e-9


@dataclass(frozen=True, slots=True)
class Chain:
    """An assembled absorbing Markov chain in canonical form."""

    states: tuple[str, ...]
    transient: tuple[str, ...]
    absorbing: tuple[str, ...]
    index: Mapping[str, int]
    P: NDArray[np.float64]
    Q: NDArray[np.float64]
    R: NDArray[np.float64]


def _resolve(weight: EdgeWeight, attempt: int) -> float:
    if isinstance(weight, int | float):
        return float(weight)
    return float(weight(attempt))


def assemble(
    augmented: AugmentedSpace,
    weights: Mapping[tuple[str, str], EdgeWeight],
    sink: str,
) -> Chain:
    """Assemble the canonical chain.

    ``weights`` maps a base edge ``(source, target)`` to a probability — a float,
    or a callable taking the attempt index. Any missing mass in a transient row is
    routed to ``sink``.
    """
    transient = tuple(s.id for s in augmented.states if not s.is_absorbing)
    absorbing = tuple(s.id for s in augmented.states if s.is_absorbing)
    states = transient + absorbing
    index = {state_id: position for position, state_id in enumerate(states)}

    if sink not in index:
        raise InvalidStateSpace(f"sink {sink!r} is not a state")
    if not set(absorbing) <= set(index):
        raise InvalidStateSpace("absorbing states missing from index")

    size = len(states)
    matrix = np.zeros((size, size), dtype=np.float64)

    for source in transient:
        outgoing: dict[str, float] = {}
        for edge in augmented.edges:
            if edge.source != source:
                continue
            key = (edge.base_source, edge.base_target)
            if key not in weights:
                raise InvalidStateSpace(
                    f"no probability for edge {edge.base_source} -> {edge.base_target}",
                )
            weight = _resolve(weights[key], edge.attempt)
            outgoing[edge.target] = outgoing.get(edge.target, 0.0) + weight

        total = sum(outgoing.values())
        if total > 1.0 + _TOL:
            raise InvalidStateSpace(
                f"row {source!r} overflows: probabilities sum to {total:.6f}",
            )
        remainder = 1.0 - total
        if remainder > _TOL:
            outgoing[sink] = outgoing.get(sink, 0.0) + remainder

        for target, probability in outgoing.items():
            if target not in index:
                raise InvalidStateSpace(f"edge {source!r} -> {target!r} is not a state")
            matrix[index[source], index[target]] = probability

    for state_id in absorbing:
        matrix[index[state_id], index[state_id]] = 1.0

    row_sums = matrix.sum(axis=1)
    if not np.allclose(row_sums, 1.0, atol=_TOL):
        raise InvalidStateSpace("assembled matrix has a row that does not sum to 1")

    transient_count = len(transient)
    return Chain(
        states=states,
        transient=transient,
        absorbing=absorbing,
        index=index,
        P=matrix,
        Q=matrix[:transient_count, :transient_count],
        R=matrix[:transient_count, transient_count:],
    )
