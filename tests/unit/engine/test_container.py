"""M13.18 (#102) — container isolation (ADR-0012 §6).

Offline tests assert the exact `docker run` invocation the engine builds. The live
run is exercised separately (it needs a Docker daemon).
"""

from __future__ import annotations

import pytest

from markov_ci.engine.container import (
    CONTAINER_WORKDIR,
    container_command,
    non_root_user,
)


def _argv() -> list[str]:
    return container_command(
        image="python:3.12-slim",
        clone="/tmp/clone-abc",
        command=["pytest", "-q"],
        user="1000:1000",
    )


def test_container_command_uses_docker_run() -> None:
    assert _argv()[:3] == ["docker", "run", "--rm"]


def test_container_command_disables_the_network() -> None:
    assert "--network=none" in _argv()


def test_container_command_has_a_read_only_root_and_tmpfs_workdir() -> None:
    argv = _argv()
    assert "--read-only" in argv
    # tmpfs work dir + tmp
    assert argv[argv.index("--tmpfs") + 1].startswith(CONTAINER_WORKDIR)
    assert argv.count("--tmpfs") == 2
    assert "/tmp" in argv


def test_container_command_runs_non_root() -> None:
    argv = _argv()
    assert argv[argv.index("--user") + 1] == "1000:1000"


def test_container_command_mounts_the_checkout_read_only() -> None:
    assert "/tmp/clone-abc:/src:ro" in _argv()


def test_container_command_runs_the_command_in_a_tmpfs_copy() -> None:
    argv = _argv()
    assert argv[-len(["pytest", "-q"]) :] == ["pytest", "-q"]
    assert 'exec "$@"' in " ".join(argv)
    assert argv[argv.index("-w") + 1] == CONTAINER_WORKDIR


def test_non_root_user_is_not_root() -> None:
    assert not non_root_user().startswith("0:")


def test_non_root_user_is_forced_off_root(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    monkeypatch.setattr(os, "getuid", lambda: 0, raising=False)
    monkeypatch.setattr(os, "getgid", lambda: 0, raising=False)
    assert non_root_user() == "65534:65534"
