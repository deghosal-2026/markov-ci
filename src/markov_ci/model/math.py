"""The chain math behind the forecasts (docs/spec/0002-matrix-assembly.md §2).

* ``N = (I - Q)^-1``     fundamental matrix — expected visits per transient state
* ``B = N @ R``          absorption probabilities per outcome
* ``t = N @ 1``          expected steps to absorption
* ``C = N @ c``          expected cost for a per-state cost vector
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from markov_ci.model.assemble import Chain

Vector = NDArray[np.float64]


def split(chain: Chain) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return the canonical ``(Q, R)`` split of the chain."""
    return chain.Q, chain.R


def fundamental(q: NDArray[np.float64]) -> NDArray[np.float64]:
    """``N = (I - Q)^-1`` — expected number of visits to each transient state."""
    size = q.shape[0]
    identity = np.eye(size, dtype=np.float64)
    visits = np.linalg.inv(identity - q)
    return visits.astype(np.float64)


def absorption(chain: Chain) -> NDArray[np.float64]:
    """``B = N @ R`` — probability of ending in each absorbing state."""
    return fundamental(chain.Q) @ chain.R


def steps_to_absorb(chain: Chain) -> Vector:
    """``t = N @ 1`` — expected number of hops before absorption."""
    visits = fundamental(chain.Q)
    return visits @ np.ones(visits.shape[0], dtype=np.float64)


def _cost_vector(
    chain: Chain,
    costs: Mapping[str, float] | Sequence[float],
) -> Vector:
    if isinstance(costs, Mapping):
        try:
            values = [float(costs[state_id]) for state_id in chain.transient]
        except KeyError as exc:  # pragma: no cover - message built below
            raise KeyError(f"no cost for transient state {exc.args[0]!r}") from exc
        return np.array(values, dtype=np.float64)
    values = [float(value) for value in costs]
    if len(values) != len(chain.transient):
        raise ValueError(
            f"expected {len(chain.transient)} costs, got {len(values)}",
        )
    return np.array(values, dtype=np.float64)


def expected_cost(
    chain: Chain,
    costs: Mapping[str, float] | Sequence[float],
) -> Vector:
    """``C = N @ c`` — expected cost per start state, given per-state costs."""
    vector = _cost_vector(chain, costs)
    return fundamental(chain.Q) @ vector
