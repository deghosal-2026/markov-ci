"""M8.1 (#37) — Monte-Carlo cross-check of the analytic forecast (spec 0002 §4)."""

from __future__ import annotations

import pytest

from markov_ci.config import chain_from_config
from markov_ci.data import load_default_config
from markov_ci.model import absorption, steps_to_absorb
from markov_ci.model.montecarlo import MonteCarloResult, monte_carlo


@pytest.fixture
def chain():  # type: ignore[no-untyped-def]
    return chain_from_config(load_default_config(), category="default")


def test_result_shape(chain) -> None:  # type: ignore[no-untyped-def]
    result = monte_carlo(chain, runs=2000, seed=1)
    assert isinstance(result, MonteCarloResult)
    assert result.runs == 2000
    assert set(result.absorption) == set(chain.absorbing)


def test_absorption_probabilities_sum_to_one(chain) -> None:  # type: ignore[no-untyped-def]
    result = monte_carlo(chain, runs=5000, seed=2)
    assert sum(result.absorption.values()) == pytest.approx(1.0, abs=1e-9)


def test_converges_to_the_analytic_absorption_probabilities(chain) -> None:  # type: ignore[no-untyped-def]
    result = monte_carlo(chain, runs=20_000, seed=3)
    analytic = absorption(chain)
    row = chain.transient.index("s0_deterministic_verify")
    for column, state_id in enumerate(chain.absorbing):
        assert result.absorption[state_id] == pytest.approx(
            float(analytic[row, column]), abs=0.02,
        )


def test_confidence_interval_contains_the_analytic_steps(chain) -> None:  # type: ignore[no-untyped-def]
    result = monte_carlo(chain, runs=20_000, seed=4)
    analytic_steps = float(steps_to_absorb(chain)[chain.transient.index("s0_deterministic_verify")])
    low, high = result.steps_ci
    assert low <= analytic_steps <= high


def test_is_deterministic(chain) -> None:  # type: ignore[no-untyped-def]
    assert monte_carlo(chain, runs=1000, seed=5) == monte_carlo(chain, runs=1000, seed=5)


def test_unknown_start_state_is_rejected(chain) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="start"):
        monte_carlo(chain, runs=10, start="does_not_exist")


def test_non_positive_runs_is_rejected(chain) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="runs"):
        monte_carlo(chain, runs=0)
