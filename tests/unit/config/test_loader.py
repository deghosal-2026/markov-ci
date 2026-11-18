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


def _with_harness(template: str) -> str:
    return VALID + (
        "\nagent:\n  adapter: harness\n  harness:\n"
        f"    command_template: {template}\n"
    )


def test_a_valid_harness_template_is_accepted() -> None:
    config = parse_config(_with_harness("'claude -p --output-format json %PROMPT%'"))
    assert config.agent.harness is not None
    assert config.agent.harness.command_template.endswith("%PROMPT%")


def test_empty_harness_template_is_rejected() -> None:
    with pytest.raises(ConfigError, match="empty"):
        parse_config(_with_harness("''"))


def test_unparseable_harness_template_is_rejected() -> None:
    # an unbalanced quote is not parseable by shlex
    with pytest.raises(ConfigError, match="parseable|unbalanced|quote"):
        parse_config(_with_harness("'harness --msg \"%PROMPT%'"))


def test_harness_template_without_a_prompt_placeholder_is_rejected() -> None:
    with pytest.raises(ConfigError, match="%PROMPT%"):
        parse_config(_with_harness("'harness --msg fixed'"))


def test_harness_template_using_the_prompt_as_program_is_rejected() -> None:
    with pytest.raises(ConfigError, match="program"):
        parse_config(_with_harness("'%PROMPT% --flag'"))


def _harness(template: str) -> str:
    import json

    return _with_harness(json.dumps(template))


@pytest.mark.parametrize("shell", ["sh", "bash", "zsh", "dash", "pwsh", "powershell", "cmd"])
def test_shell_reentry_with_the_prompt_in_the_c_script_is_rejected(shell: str) -> None:
    # M13.3 (#87): a shell that would re-parse the prompt is rejected (ADR-0016 §5).
    with pytest.raises(ConfigError, match="shell"):
        parse_config(_harness(f"{shell} -c 'tool %PROMPT%'"))


def test_cmd_reentry_uses_the_windows_c_flag() -> None:
    with pytest.raises(ConfigError, match="shell"):
        parse_config(_harness("cmd /c 'tool %PROMPT%'"))


def test_a_shell_program_without_c_is_allowed() -> None:
    # No `-c` / `/c`: the prompt is an ordinary argument, not a script.
    config = parse_config(_harness("bash wrapper.sh %PROMPT%"))
    assert config.agent.harness is not None


def test_the_safe_positional_shell_form_is_allowed() -> None:
    # ADR-0016 §5: `bash -c 'tool "$1"' _ %PROMPT%` keeps the prompt positional.
    config = parse_config(_harness("""bash -c 'tool "$1"' _ %PROMPT%"""))
    assert config.agent.harness is not None


def test_prompt_file_only_template_is_accepted() -> None:
    # M13.4 (#88): %PROMPT_FILE% is a valid placeholder (prompt off argv).
    config = parse_config(_harness("harness --prompt-file %PROMPT_FILE%"))
    assert config.agent.harness is not None


def test_harness_name_sets_the_adapter_id() -> None:
    # M13.19 (#103): the harness reports its template name, not a generic "harness".
    text = VALID + (
        "\nagent:\n  adapter: harness\n  harness:\n    name: claude-code\n"
        "    command_template: 'claude -p %PROMPT%'\n"
    )
    config = parse_config(text)
    assert config.agent.harness is not None
    assert config.agent.harness.name == "claude-code"


def test_prior_success_outside_the_unit_interval_is_rejected() -> None:
    # M13.30 (#114)
    broken = VALID + (
        "\npriors:\n  default:\n    default: { success: [1.5, 0.5, 0.2] }\n"
    )
    with pytest.raises(ConfigError, match="within \\[0, 1\\]"):
        parse_config(broken)


def test_version_is_checked_before_the_schema() -> None:
    # a v2 document fails with a version message, not a schema error
    with pytest.raises(ConfigError, match="version"):
        parse_config("version: 2\nstates: {}\ntransitions: []\n")


def test_the_dead_cost_weight_key_is_rejected() -> None:
    # M13.31 (#115): cost_weight was dead config; it is no longer accepted.
    broken = VALID + "\npriors:\n  default:\n    default: { success: [0.9], cost_weight: 2.5 }\n"
    with pytest.raises(ConfigError, match="cost_weight"):
        parse_config(broken)


def test_invalid_yaml_is_reported() -> None:
    with pytest.raises(ConfigError, match="invalid YAML"):
        parse_config("version: 1\nstates: {a: [unclosed\n")


def test_an_unknown_key_without_a_line_is_still_reported() -> None:
    # `_line_of` returns None for a key not present verbatim; the error still fires
    with pytest.raises(ConfigError):
        parse_config(VALID + "\npolicy:\n  bogus: 1\n")
