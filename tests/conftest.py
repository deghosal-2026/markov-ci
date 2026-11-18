"""Test configuration.

Put `src/` on the import path so the suite runs from a checkout without an editable
install (mirrors the `pythonpath` setting added to pyproject.toml in M0.2).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _ensure_git_repo(path: Path) -> None:
    """Make an example's demo tree a real git repo (validation uses worktrees)."""
    if (path / ".git").exists():
        return
    for args in (
        ("init", "-q"),
        ("config", "user.email", "demo@example.com"),
        ("config", "user.name", "markov-ci demo"),
        ("add", "-A"),
        ("commit", "-qm", "demo baseline"),
    ):
        subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


@pytest.fixture(scope="session", autouse=True)
def _example_repos_are_git() -> None:
    """Materialize every `examples/<NN>-*/repo` once, so the documented run
    commands execute verbatim (docs-are-tests) and the proof-suite enforcer can
    drive real worktree validation."""
    examples = Path(__file__).resolve().parents[1] / "examples"
    for repo in sorted(examples.glob("[0-9][0-9]-*/repo")):
        if repo.is_dir():
            _ensure_git_repo(repo)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block outbound sockets so the whole suite proves it runs offline (M13.41)."""
    import socket

    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("network access is blocked in the test suite")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
