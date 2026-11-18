"""Compile a validated `Config` into an executable `Chain`.

This is the bridge between the user's declarative config and the model: it turns
states + transitions + priors into the augmented, assembled Markov chain that the
math (and the runtime) operate on.

The engine's *escalation sink* is resolved to the absorbing state whose id names
escalation (``a2_escalate_to_author``); if none is found, the first absorbing state
is used.
"""

from __future__ import annotations

from collections.abc import Callable

from markov_ci.config.models import Config
from markov_ci.model import (
    Chain,
    EdgeWeight,
    State,
    StateSpace,
    StateType,
    TransitionEdge,
    assemble,
    augment,
)


class ConfigCompileError(ValueError):
    """Raised when a config cannot be compiled into a chain."""


def success_curve(config: Config, adapter: str, category: str) -> tuple[float, ...]:
    """Public accessor for the prior success curve of (adapter, category)."""
    return _success_curve(config, adapter, category)


def _success_curve(config: Config, adapter: str, category: str) -> tuple[float, ...]:
    # resolution: priors[adapter][category] -> priors["default"][category] -> error
    adapter_block = config.priors.get(adapter)
    if adapter_block is None:
        adapter_block = config.priors.get("default")
    if adapter_block is None:
        raise ConfigCompileError(f"no priors for adapter {adapter!r}")
    prior = adapter_block.get(category)
    if prior is None:
        raise ConfigCompileError(
            f"no prior for category {category!r} (adapter {adapter!r})",
        )
    if len(prior.success) < config.policy.max_attempts:
        raise ConfigCompileError(
            f"prior {category!r} has {len(prior.success)} attempts but "
            f"max_attempts is {config.policy.max_attempts}",
        )
    return tuple(prior.success)


def _gated_curve(
    success: tuple[float, ...], min_confidence: float,
) -> Callable[[int], float]:
    """The prior curve with the confidence gate applied (spec 0004, M13.27).

    An attempt whose success probability is below ``min_confidence`` never reaches
    the sandbox: its ``s2#k`` edge is zeroed, so the row's mass routes to the
    escalation sink — exactly what the runtime gate does.
    """
    def _weight(attempt: int) -> float:
        value = success[attempt - 1]
        return value if value >= min_confidence else 0.0

    return _weight


def confidence_gate_warnings(
    config: Config, adapter: str = "default", category: str = "default",
) -> tuple[str, ...]:
    """Warn when the confidence gate makes ``max_attempts`` unreachable (M13.27)."""
    curve = _success_curve(config, adapter, category)
    min_confidence = config.policy.min_confidence
    for attempt in range(1, config.policy.max_attempts + 1):
        if curve[attempt - 1] < min_confidence:
            return (
                f"attempt {attempt}: success {curve[attempt - 1]:.2f} < "
                f"min_confidence {min_confidence:.2f} — the gate escalates to a2, "
                f"so max_attempts ({config.policy.max_attempts}) is unreachable",
            )
    return ()


def _sink(config: Config) -> str:
    absorbing = list(config.absorbing_ids)
    for state_id in absorbing:
        if "escalate" in state_id:
            return state_id
    if absorbing:
        return absorbing[0]
    raise ConfigCompileError("config has no absorbing state to use as a sink")


def chain_from_config(
    config: Config,
    *,
    category: str = "default",
    adapter: str = "default",
) -> Chain:
    """Compile ``config`` into a `Chain` for the given failure category/adapter."""
    space = StateSpace.of(
        *(
            State(
                id=state_id,
                type=StateType(state.type),
                loop_capable=state.loop_capable,
            )
            for state_id, state in config.states.items()
        ),
    )
    edges = tuple(
        TransitionEdge(source=t.source, target=t.target, per_attempt=t.per_attempt)
        for t in config.transitions
    )

    weights: dict[tuple[str, str], EdgeWeight] = {}
    for transition in config.transitions:
        key = (transition.source, transition.target)
        if transition.prior_driven:
            weights[key] = _gated_curve(
                _success_curve(config, adapter, category),
                config.policy.min_confidence,
            )
        else:
            assert transition.probability is not None  # guaranteed by the model
            weights[key] = transition.probability

    augmented = augment(space, edges, max_attempts=config.policy.max_attempts)
    return assemble(augmented, weights, sink=_sink(config))
