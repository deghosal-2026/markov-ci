"""M13.14 (#98) — environment scrubbing for untrusted child processes (ADR-0012 §2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from markov_ci.scrub import is_secret, scrubbed_env


def test_secret_detection() -> None:
    assert is_secret("GITHUB_TOKEN")
    assert is_secret("ACTIONS_RUNTIME_TOKEN")
    assert is_secret("MY_API_KEY")
    assert is_secret("DB_SECRET")
    assert not is_secret("PATH")
    assert not is_secret("MY_PROVIDER")


def test_base_env_keeps_only_path_lang_and_a_temp_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("LANG", "C.UTF-8")
    monkeypatch.setenv("EDITOR", "vim")
    env = scrubbed_env(home=Path("/tmp/home"))
    assert env["PATH"] == "/usr/bin"
    assert env["LANG"] == "C.UTF-8"
    assert env["HOME"] == "/tmp/home"
    assert "EDITOR" not in env


def test_secrets_are_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN", "MY_KEY", "DB_SECRET"):
        monkeypatch.setenv(name, "leaked")
    env = scrubbed_env(home=Path("/tmp/home"))
    for leaked in ("GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN", "MY_KEY", "DB_SECRET"):
        assert leaked not in env


def test_config_listed_vars_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_PROVIDER_KEY", "value")
    env = scrubbed_env(home=Path("/tmp/home"), allow=("MY_PROVIDER_KEY",))
    assert env["MY_PROVIDER_KEY"] == "value"


def test_hard_blocked_vars_never_pass_even_if_listed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "leaked")
    monkeypatch.setenv("ACTIONS_ID_TOKEN", "leaked")
    env = scrubbed_env(
        home=Path("/tmp/home"), allow=("GITHUB_TOKEN", "ACTIONS_ID_TOKEN"),
    )
    assert "GITHUB_TOKEN" not in env
    assert "ACTIONS_ID_TOKEN" not in env


def test_scrubbed_env_uses_the_provided_base(monkeypatch: pytest.MonkeyPatch) -> None:
    env = scrubbed_env(home=Path("/tmp/home"), base={"PATH": "/bin", "GITHUB_TOKEN": "x"})
    assert env == {"PATH": "/bin", "HOME": "/tmp/home"}
