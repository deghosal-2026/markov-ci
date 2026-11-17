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


def _success_curve(config: Config, adapter: str, category: str) -> tuple[float, ...]:
    adapter_block = config.priors.get(adapter)
    if adapter_block is None:
        adapter_block = config.priors.get("default")
    if adapter_block is None:
        raise ConfigCompileError(f"no priors for adapter {adapter!r}")
    prior = adapter_block.get(category) or adapter_block.get("default")
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


def _curve(success: tuple[float, ...]) -> Callable[[int], float]:
    return lambda attempt: success[attempt - 1]


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
            weights[key] = _curve(_success_curve(config, adapter, category))
        else:
            assert transition.probability is not None  # guaranteed by the model
            weights[key] = transition.probability

    augmented = augment(space, edges, max_attempts=config.policy.max_attempts)
    return assemble(augmented, weights, sink=_sink(config))
