"""M2.2 (#16) — YAML config loader (docs/spec/0003-config-format.md)."""

from __future__ import annotations

import pytest

from markov_ci.config import Config, ConfigError, parse_config

VALID = """
version: 1
states:
  s0_deterministic_verify: { type: transient }
  s1_failure_triage: { type: transient }
  s2_agent_reasoning: { type: transient, loop_capable: true }
  s3_sandbox_validation: { type: transient, loop_capable: true }
  s4_regression_check: { type: transient }
  a1_ready_for_human_review: { type: absorbing }
  a2_escalate_to_author: { type: absorbing }
  a3_budget_exceeded: { type: absorbing }
transitions:
  - { from: s0_deterministic_verify, to: a1_ready_for_human_review, probability: 0.82 }
  - { from: s0_deterministic_verify, to: s1_failure_triage, probability: 0.18 }
  - { from: s1_failure_triage, to: s2_agent_reasoning, probability: 0.75 }
  - { from: s1_failure_triage, to: a2_escalate_to_author, probability: 0.25 }
  - { from: s3_sandbox_validation, to: s4_regression_check, probability: 0.65 }
  - { from: s3_sandbox_validation, to: s2_agent_reasoning, probability: 0.25, per_attempt: true }
  - { from: s3_sandbox_validation, to: a2_escalate_to_author, probability: 0.10 }
  - { from: s4_regression_check, to: a1_ready_for_human_review, probability: 0.90 }
  - { from: s4_regression_check, to: a2_escalate_to_author, probability: 0.10 }
policy:
  min_confidence: 0.40
  max_attempts: 3
"""


def test_parses_a_valid_config() -> None:
    config = parse_config(VALID)
    assert isinstance(config, Config)
    assert config.version == 1
    assert len(config.states) == 8
    assert config.policy.max_attempts == 3


def test_version_defaults_to_one() -> None:
    config = parse_config(VALID.replace("version: 1\n", ""))
    assert config.version == 1


def test_policy_defaults_apply() -> None:
    config = parse_config(VALID)
    assert config.policy.min_confidence == 0.40
    assert config.policy.max_tokens == 200_000


def test_the_redundant_command_adapter_value_is_rejected() -> None:
    # spec 0006 §3: BYO commands go through `harness` + command_template, not a
    # separate `command` adapter value (there is no such adapter in the engine).
    broken = VALID + "\nagent:\n  adapter: command\n"
    with pytest.raises(ConfigError):
        parse_config(broken)


def test_unknown_top_level_key_is_rejected_with_a_line() -> None:
    with pytest.raises(ConfigError) as excinfo:
        parse_config(VALID + "\nbogus_key: 1\n")
    assert "bogus_key" in str(excinfo.value)
    assert "line" in str(excinfo.value).lower()


def test_unknown_nested_key_is_rejected() -> None:
    broken = VALID.replace(
        "s0_deterministic_verify: { type: transient }",
        "s0_deterministic_verify: { type: transient, wat: true }",
    )
    with pytest.raises(ConfigError) as excinfo:
        parse_config(broken)
    assert "wat" in str(excinfo.value)


def test_wrong_version_is_rejected() -> None:
    with pytest.raises(ConfigError, match="version"):
        parse_config(VALID.replace("version: 1", "version: 2"))


def test_transition_referencing_unknown_state_is_rejected() -> None:
    broken = VALID.replace("to: s1_failure_triage", "to: does_not_exist")
    with pytest.raises(ConfigError, match="does_not_exist"):
        parse_config(broken)


def test_edge_leaving_an_absorbing_state_is_rejected() -> None:
    bad_edge = (
        "  - { from: a1_ready_for_human_review, to: s0_deterministic_verify, probability: 0.1 }\n"
    )
    broken = VALID.replace(
        "  - { from: s4_regression_check, to: a2_escalate_to_author, probability: 0.10 }\n",
        "  - { from: s4_regression_check, to: a2_escalate_to_author, probability: 0.10 }\n"
        + bad_edge,
    )
    with pytest.raises(ConfigError, match="absorbing"):
        parse_config(broken)


def test_pre_augmented_state_id_is_rejected() -> None:
    broken = VALID.replace("from: s3_sandbox_validation, to: s4_regression_check",
                           "from: s3_sandbox_validation#1, to: s4_regression_check")
    with pytest.raises(ConfigError, match="#"):
        parse_config(broken)


def test_empty_document_is_rejected() -> None:
    with pytest.raises(ConfigError):
        parse_config("")


def test_non_mapping_document_is_rejected() -> None:
    with pytest.raises(ConfigError):
        parse_config("- just\n- a list\n")


def test_error_is_a_value_error() -> None:
    assert issubclass(ConfigError, ValueError)
