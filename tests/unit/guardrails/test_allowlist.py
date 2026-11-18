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


def test_env_variants_are_denied() -> None:
    # M13.12 (#96): `.env*` / `**/.env*` — tested under allow_write=("**",) so
    # the always-denied set is the only reason to deny.
    for path in (".env.local", "config/.env.production", ".envrc", ".env"):
        assert check_paths([path], allow_write=("**",)).allowed is False, path


def test_codeowners_is_denied() -> None:
    for path in ("CODEOWNERS", "docs/CODEOWNERS", ".github/CODEOWNERS"):
        assert check_paths([path], allow_write=("**",)).allowed is False, path


def test_key_and_credential_files_are_denied() -> None:
    for path in (
        "src/deploy.pem",
        "config/service.key",
        "home/.ssh/id_rsa",
        ".aws/credentials",
        "ops/service-account.json",
        "cert/server.p12",
    ):
        assert check_paths([path], allow_write=("**",)).allowed is False, path


def test_common_ci_configs_are_denied() -> None:
    for path in (
        ".gitlab-ci.yml",
        ".travis.yml",
        "azure-pipelines.yml",
        "Jenkinsfile",
        ".circleci/config.yml",
        ".buildkite/pipeline.yml",
        "bitbucket-pipelines.yml",
    ):
        assert check_paths([path], allow_write=("**",)).allowed is False, path


def test_common_build_configs_are_denied() -> None:
    for path in (
        "Dockerfile",
        "docker-compose.yml",
        "Makefile",
        "pyproject.toml",
        "setup.py",
        "tox.ini",
        ".pre-commit-config.yaml",
    ):
        assert check_paths([path], allow_write=("**",)).allowed is False, path


def test_matching_is_case_insensitive() -> None:
    assert check_paths([".GITHUB/workflows/ci.yml"], allow_write=("**",)).allowed is False
    assert check_paths(["License"], allow_write=("**",)).allowed is False
    assert check_paths(["CONFIG.ENV"], allow_write=("**",)).allowed is False
    assert check_paths(["SRC/Deploy.PEM"], allow_write=("**",)).allowed is False


def test_adversarial_paths_are_denied_even_under_a_wildcard_allowlist() -> None:
    # M13.39 (#123): the always-denied set is the only guard when allow_write=("**",)
    for path in (
        ".github/workflows/ci.yml",
        ".env",
        ".env.local",
        "secrets/token",
        "LICENSE",
        "package-lock.json",
        "id_rsa",
        "src/deploy.pem",
        "src/../../etc/passwd",
        "/etc/passwd",
    ):
        assert check_paths([path], allow_write=("**",)).allowed is False, path
