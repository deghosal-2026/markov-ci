"""M0.3 — the Makefile exposes the local quality gate on real tools."""

from __future__ import annotations

import re
from pathlib import Path

MAKEFILE = Path(__file__).resolve().parents[2] / "Makefile"

REQUIRED_TARGETS = ("test", "lint", "typecheck", "cov", "docs", "build", "clean", "help")


def _text() -> str:
    return MAKEFILE.read_text(encoding="utf-8")


def test_makefile_exists() -> None:
    assert MAKEFILE.is_file()


def test_every_required_target_is_declared() -> None:
    text = _text()
    missing = [t for t in REQUIRED_TARGETS if not re.search(rf"^{t}:", text, re.MULTILINE)]
    assert missing == [], f"missing targets: {missing}"


def test_targets_are_phony() -> None:
    phony = next(
        (ln for ln in _text().splitlines() if ln.startswith(".PHONY")),
        "",
    )
    missing = [t for t in REQUIRED_TARGETS if t not in phony]
    assert missing == [], f"not declared .PHONY: {missing}"


def test_targets_invoke_real_tools() -> None:
    text = _text()
    for tool in ("pytest", "ruff", "mypy", "mkdocs", "-m build"):
        assert tool in text, f"{tool} not wired"


def test_gate_targets_do_not_swallow_failures() -> None:
    text = _text()
    assert "|| true" not in text
    assert "; true" not in text


def test_help_is_the_default_goal() -> None:
    assert ".DEFAULT_GOAL := help" in _text()
