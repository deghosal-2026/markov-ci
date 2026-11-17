"""M2.3 (#17) — the packaged default config (docs/spec/0001-state-model.md §3–4)."""

from __future__ import annotations

from importlib import resources

import pytest

from markov_ci.config import chain_from_config, load_config
from markov_ci.data import default_config_path, load_default_config
from markov_ci.model import absorption


def test_default_config_resource_ships_with_the_package() -> None:
    resource = resources.files("markov_ci.data").joinpath("default.yaml")
    assert resource.is_file()


def test_default_config_path_points_at_a_real_file() -> None:
    path = default_config_path()
    assert path.is_file()
    assert path.name == "default.yaml"


def test_load_default_config_parses_and_validates() -> None:
    config = load_default_config()
    assert config.version == 1
    assert config.policy.max_attempts == 3
    assert config.policy.min_confidence == 0.40


def test_default_states_match_the_spec() -> None:
    config = load_default_config()
    assert set(config.states) == {
        "s0_deterministic_verify",
        "s1_failure_triage",
        "s2_agent_reasoning",
        "s3_sandbox_validation",
        "s4_regression_check",
        "a1_ready_for_human_review",
        "a2_escalate_to_author",
        "a3_budget_exceeded",
    }
    assert config.states["s2_agent_reasoning"].loop_capable is True


def test_default_priors_match_the_spec() -> None:
    config = load_default_config()
    default_priors = config.priors["default"]
    assert default_priors["lint_error"].success == [0.92, 0.65, 0.20]
    assert default_priors["unit_assertion"].success == [0.74, 0.45, 0.15]
    assert default_priors["infra_timeout"].success == [0.05, 0.01, 0.00]
    assert all(prior.source == "prior" for prior in default_priors.values())


def test_loading_by_path_matches_packaged_default() -> None:
    from_path = load_config(default_config_path())
    assert from_path.states.keys() == load_default_config().states.keys()


def test_prior_driven_edge_is_declared_for_s2_to_s3() -> None:
    config = load_default_config()
    prior_edges = [
        t for t in config.transitions if t.prior_driven
    ]
    assert [(t.source, t.target) for t in prior_edges] == [
        ("s2_agent_reasoning", "s3_sandbox_validation")
    ]


def test_compiled_default_chain_reproduces_the_golden_numbers() -> None:
    chain = chain_from_config(load_default_config(), category="default")
    b = absorption(chain)
    given_s0 = float(b[chain.transient.index("s0_deterministic_verify"),
                       chain.absorbing.index("a1_ready_for_human_review")])
    given_s2 = float(b[chain.transient.index("s2_agent_reasoning#1"),
                       chain.absorbing.index("a1_ready_for_human_review")])
    assert given_s0 == pytest.approx(0.92, abs=0.01)
    assert given_s2 == pytest.approx(0.72, abs=0.01)
