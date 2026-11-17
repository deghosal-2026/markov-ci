"""M5.1 (#26) — write allowlist + always-denied set (docs/spec/0005-guardrails.md §1)."""

from __future__ import annotations

from markov_ci.guardrails.allowlist import (
    ALWAYS_DENIED,
    DEFAULT_ALLOW_WRITE,
    GuardrailDecision,
    check_paths,
)


def test_default_allowlist_permits_source_and_tests() -> None:
    decision = check_paths(["src/markov_ci/model/state.py", "tests/unit/test_x.py"])
    assert decision.allowed is True
    assert decision.offending == ()


def test_path_outside_the_allowlist_is_denied() -> None:
    decision = check_paths(["docs/readme.md"])
    assert decision.allowed is False
    assert "docs/readme.md" in decision.offending[0]


def test_ci_config_is_denied() -> None:
    assert check_paths([".github/workflows/ci.yml"]).allowed is False


def test_secrets_directory_is_denied() -> None:
    assert check_paths(["src/secrets/key.pem"]).allowed is False


def test_env_file_is_denied() -> None:
    assert check_paths(["config.env"]).allowed is False


def test_license_is_denied() -> None:
    assert check_paths(["LICENSE"]).allowed is False


def test_absolute_path_is_denied() -> None:
    assert check_paths(["/etc/passwd"]).allowed is False


def test_path_traversal_is_denied() -> None:
    assert check_paths(["src/../../etc/passwd"]).allowed is False


def test_always_denied_cannot_be_widened_by_allow_write() -> None:
    decision = check_paths(
        [".github/workflows/ci.yml"],
        allow_write=(*DEFAULT_ALLOW_WRITE, ".github/**"),
    )
    assert decision.allowed is False


def test_always_denied_cannot_be_widened_by_deny_write() -> None:
    # deny_write can only add denials, never remove the built-in set
    decision = check_paths(["LICENSE"], deny_write=())
    assert decision.allowed is False


def test_custom_deny_write_adds_denials() -> None:
    decision = check_paths(["src/generated/x.py"], deny_write=("src/generated/**",))
    assert decision.allowed is False


def test_multiple_offenders_are_all_reported() -> None:
    decision = check_paths(["LICENSE", "src/ok.py", ".github/x.yml"])
    assert decision.allowed is False
    assert len(decision.offending) == 2


def test_decision_type() -> None:
    assert isinstance(check_paths(["src/a.py"]), GuardrailDecision)


def test_always_denied_set_is_non_empty_with_ci_rules() -> None:
    assert any(".github" in pattern for pattern in ALWAYS_DENIED)
    assert any("secret" in pattern for pattern in ALWAYS_DENIED)


def test_is_deterministic() -> None:
    files = ["LICENSE", "src/a.py", ".github/x"]
    assert check_paths(files) == check_paths(files)


def test_windows_style_backslashes_are_normalized() -> None:
    assert check_paths(["src\\..\\..\\etc\\passwd"]).allowed is False
