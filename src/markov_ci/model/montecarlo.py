"""Monte-Carlo simulation of a chain (docs/spec/0002-matrix-assembly.md §4).

An independent, simulation-based path to the same numbers the analytic math
produces — two implementations agreeing is evidence, one is a claim.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from markov_ci.model.assemble import Chain
from markov_ci.model.posterior import norm_ppf


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    """Empirical absorption/cost statistics from many simulated runs."""

    runs: int
    absorption: Mapping[str, float]
    mean_steps: float
    steps_ci: tuple[float, float]
    mean_cost: float
    cost_ci: tuple[float, float]


def _mean_ci(values: Sequence[float], level: float) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    if n == 1:
        return mean, mean
    variance = sum((value - mean) ** 2 for value in values) / (n - 1)
    half = norm_ppf(1 - (1 - level) / 2) * (variance / n) ** 0.5
    return mean - half, mean + half


def monte_carlo(  # noqa: PLR0913
    chain: Chain,
    *,
    runs: int = 10_000,
    seed: int = 0,
    start: str | None = None,
    cost_of: Mapping[str, float] | None = None,
    level: float = 0.95,
) -> MonteCarloResult:
    """Simulate ``runs`` journeys through the chain and report the statistics."""
    if runs < 1:
        raise ValueError(f"runs must be >= 1, got {runs}")
    start_state = start or (chain.transient[0] if chain.transient else None)
    if start_state is None or start_state not in chain.index:
        raise ValueError(f"unknown start state: {start!r}")

    costs = cost_of or dict.fromkeys(chain.transient, 1.0)
    rng = random.Random(seed)
    absorption_counts = dict.fromkeys(chain.absorbing, 0)
    steps: list[float] = []
    total_costs: list[float] = []

    for _ in range(runs):
        state = start_state
        step_count = 0
        cost = 0.0
        while state not in chain.absorbing:
            position = chain.index[state]
            cost += float(costs.get(state, 0.0))
            thresholds = chain.P[position]
            draw = rng.random()
            cumulative = 0.0
            for target, probability in zip(chain.states, thresholds, strict=True):
                cumulative += float(probability)
                if draw <= cumulative:
                    state = target
                    break
            step_count += 1
        absorption_counts[state] += 1
        steps.append(float(step_count))
        total_costs.append(cost)

    return MonteCarloResult(
        runs=runs,
        absorption={
            state_id: count / runs for state_id, count in absorption_counts.items()
        },
        mean_steps=sum(steps) / runs,
        steps_ci=_mean_ci(steps, level),
        mean_cost=sum(total_costs) / runs,
        cost_ci=_mean_ci(total_costs, level),
    )
