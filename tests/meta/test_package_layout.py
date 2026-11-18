"""M0.1 — the package tree exists, imports cleanly, and ships `py.typed`.

These tests are the executable form of the M0.1 acceptance criteria in `docs/WBS.md`.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import markov_ci

# The module map documented in docs/architecture.md.
SUBPACKAGES = (
    "model",
    "policy",
    "triage",
    "agents",
    "guardrails",
    "engine",
    "telemetry",
    "queueing",
    "config",
    "data",
    "cli",
)


def _package_dir() -> Path:
    return Path(markov_ci.__file__).parent


def test_package_imports() -> None:
    assert markov_ci.__name__ == "markov_ci"


def test_subpackages_are_importable() -> None:
    for name in SUBPACKAGES:
        module = importlib.import_module(f"markov_ci.{name}")
        assert module.__name__ == f"markov_ci.{name}"


def test_subpackages_have_init_files() -> None:
    base = _package_dir()
    missing = [name for name in SUBPACKAGES if not (base / name / "__init__.py").is_file()]
    assert missing == [], f"missing package __init__.py for: {missing}"


def test_py_typed_is_present() -> None:
    assert (_package_dir() / "py.typed").is_file(), "markov_ci/py.typed is required (ADR-0006)"


def test_repo_layout_skeleton_exists() -> None:
    repo_root = _package_dir().parents[1]
    for rel in ("tests/unit", "tests/integration", "tests/e2e"):
        assert (repo_root / rel).is_dir(), f"missing {rel}"
