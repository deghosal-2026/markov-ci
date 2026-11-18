"""M13.27 (#111) — the confidence gate is modelled in assembly (spec 0004)."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from markov_ci.config import chain_from_config, confidence_gate_warnings
from markov_ci.data import load_default_config
from markov_ci.model import absorption, monte_carlo

CATEGORIES = ("lint_error", "type_mismatch", "unit_assertion", "infra_timeout", "default")


def test_low_confidence_attempt_is_zeroed_to_the_sink() -> None:
    # lint_error success[2] = 0.20 < min_confidence 0.40 → s2#3 never reaches s3
    chain = chain_from_config(load_default_config(), category="lint_error")
    row = chain.index["s2_agent_reasoning#3"]
    assert chain.P[row][chain.index["s3_sandbox_validation#3"]] == 0.0
    assert chain.P[row][chain.index["a2_escalate_to_author"]] == pytest.approx(1.0)


def test_high_confidence_attempt_keeps_its_edge() -> None:
    chain = chain_from_config(load_default_config(), category="lint_error")
    row = chain.index["s2_agent_reasoning#1"]
    assert chain.P[row][chain.index["s3_sandbox_validation#1"]] == pytest.approx(0.92)


def test_warns_when_the_gate_makes_max_attempts_unreachable() -> None:
    warnings = confidence_gate_warnings(load_default_config(), category="lint_error")
    assert warnings
    assert "unreachable" in warnings[0]


def test_no_warning_when_every_attempt_clears_the_gate() -> None:
    config = load_default_config()
    config = config.model_copy(
        update={
            "priors": {
                "default": {
                    "default": config.priors["default"]["default"].model_copy(
                        update={"success": [0.9, 0.9, 0.9]},
                    ),
                },
            },
        },
    )
    assert confidence_gate_warnings(config, category="default") == ()


@given(category=st.sampled_from(CATEGORIES))
@settings(max_examples=5, deadline=None)
def test_monte_carlo_of_the_gated_chain_agrees_with_the_analytic_forecast(
    category: str,
) -> None:
    chain = chain_from_config(load_default_config(), category=category)
    analytic = absorption(chain)
    mc = monte_carlo(chain, runs=20_000, seed=1)
    for column, state_id in enumerate(chain.absorbing):
        assert mc.absorption[state_id] == pytest.approx(analytic[0, column], abs=0.03)
