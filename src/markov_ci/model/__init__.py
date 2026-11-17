"""markov_ci.model — states, augmentation, assembly, and the chain math."""

from __future__ import annotations

from markov_ci.model.augment import (
    AugmentedEdge,
    AugmentedSpace,
    TransitionEdge,
    augment,
)
from markov_ci.model.state import (
    InvalidStateSpace,
    State,
    StateSpace,
    StateType,
)

__all__ = [
    "AugmentedEdge",
    "AugmentedSpace",
    "InvalidStateSpace",
    "State",
    "StateSpace",
    "StateType",
    "TransitionEdge",
    "augment",
]

