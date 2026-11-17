"""markov_ci.model — states, augmentation, assembly, and the chain math."""

from __future__ import annotations

from markov_ci.model.assemble import Chain, EdgeWeight, assemble
from markov_ci.model.augment import (
    AugmentedEdge,
    AugmentedSpace,
    TransitionEdge,
    augment,
)
from markov_ci.model.math import (
    absorption,
    expected_cost,
    fundamental,
    split,
    steps_to_absorb,
)
from markov_ci.model.posterior import Posterior, posterior
from markov_ci.model.state import (
    InvalidStateSpace,
    State,
    StateSpace,
    StateType,
)
from markov_ci.model.validate import Finding, ValidationResult, validate

__all__ = [
    "AugmentedEdge",
    "AugmentedSpace",
    "Chain",
    "EdgeWeight",
    "Finding",
    "InvalidStateSpace",
    "State",
    "StateSpace",
    "Posterior",
    "StateType",
    "TransitionEdge",
    "ValidationResult",
    "absorption",
    "assemble",
    "augment",
    "expected_cost",
    "fundamental",
    "posterior",
    "split",
    "steps_to_absorb",
    "validate",
]

